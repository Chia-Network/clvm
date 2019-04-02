import hashlib

from .casts import bls12_381_from_bytes, bls12_381_to_bytes
from .ecdsa.bls12_381 import bls12_381_generator

from .ReduceError import ReduceError
from .SExp import SExp


S_False = SExp(0)
S_True = SExp(1)


MASK_128 = ((1 << 128) - 1)


def byte_operator(f_op):
    def f(form, context):
        items = [context.reduce_f(_, context) for _ in form[1:]]
        if has_unbound_values(items):
            return SExp([form[0], *items])
        return f_op(items)
    return f


def int_operator(f_op):
    def f(form, context):
        items = [context.reduce_f(_, context) for _ in form[1:]]
        if has_unbound_values(items):
            return SExp([form[0], *items])
        return f_op([_.as_int() for _ in items])
    return f


def operator(op_f):
    def do_f_op(form, context):
        items = [context.reduce_f(_, context) for _ in form[1:]]
        return op_f(items)
    return do_f_op


def truncate_int(v):
    v1 = abs(v) & MASK_128
    if v < 0:
        v1 = -v1
    return v1


def has_unbound_values(items):
    return any(not _.is_bytes() for _ in items)


@operator
def op_cons(items):
    if len(items) == 0:
        return SExp([])
    if len(items) == 1:
        return SExp([items[0]])
    if len(items) != 2 or not items[1].is_list():
        raise ValueError("cons takes at most two parameters; the second must be a list")
    new_list = [items[0]] + list(items[1])
    return SExp(new_list)


@operator
def op_first(items):
    if len(items) != 1 or not items[0].is_list():
        raise ValueError("first takes exactly one list parameter")
    return SExp(items[0].item[0])


@operator
def op_rest(items):
    if len(items) != 1 or not items[0].is_list():
        raise ValueError("rest takes exactly one list parameter")
    return SExp(items[0].item[1])


@operator
def op_list(items):
    return SExp(items)


@operator
def op_type(items):
    if len(items) != 1:
        raise ValueError("type takes exactly one parameter")
    return SExp(items[0].type - 1)


@operator
def op_is_null(items):
    if len(items) != 1:
        raise ValueError("is_null takes exactly one parameter")
    return SExp(1 if len(items[0]) == 0 else 0)


@operator
def op_is_atom(items):
    if len(items) != 1:
        raise ValueError("is_atom takes exactly one parameter")
    return SExp(not items[0].is_list())


@operator
def op_get_default(args):
    if len(args) == 3:
        item, default, index = args
        if item.is_list() and index.is_bytes() and 0 <= index.as_int() < len(item):
            return SExp(item[index.as_int()])
        else:
            return default
    raise ReduceError("get_default takes exactly 3 parameters, got %d" % len(args))


@operator
def op_get_raw(args):
    if len(args) in (2, 3):
        item, index = args[0], args[1]
        if item.is_list() and index.is_bytes() and 0 <= index.as_int() < len(item):
            return SExp(item[index.as_int()])
        else:
            if len(args) == 3:
                return args[2]
            raise ReduceError("get_raw bad index or not list and no default set")
    raise ReduceError("get_raw takes exactly 2 or 3 parameters, got %d" % len(args))


@operator
def op_get(items):
    if len(items) < 1:
        return S_False
    item = items[0]
    for _ in items[1:]:
        if item.is_list() and _.is_bytes() and 0 <= _.as_int() < len(item):
            item = item[_.as_int()]
        else:
            return S_False
    return item


@operator
def op_wrap(items):
    if len(items) < 1:
        return S_False
    return SExp(items[0].as_bin())


@int_operator
def op_pubkey_for_exp(items):
    def blob_for_item(_):
        try:
            return bls12_381_to_bytes(bls12_381_generator * _)
        except Exception as ex:
            return b''

    if len(items) < 1:
        return S_False
    return SExp(blob_for_item(items[0]))


@byte_operator
def op_point_add(items):
    if len(items) < 1:
        return S_False
    p = bls12_381_from_bytes(items[0].as_bytes())
    for _ in items[1:]:
        p += bls12_381_from_bytes(_.as_bytes())
    return SExp(bls12_381_to_bytes(p))


@int_operator
def op_add(items):
    return SExp(sum(_ for _ in items))


@int_operator
def op_multiply(items):
    v = 1
    for _ in items:
        v = truncate_int(v * _)
    return SExp(v)


@int_operator
def op_divide(items):
    if len(items) == 0:
        return SExp(0)
    v = items[0]
    for _ in items[1:]:
        v = truncate_int(v // _)
    return SExp(v)


@int_operator
def op_subtract(items):
    if len(items) == 0:
        return SExp(0)
    v = items[0]
    for _ in items[1:]:
        v = truncate_int(v - _)
    return SExp(v)


@byte_operator
def op_sha256(items):
    h = hashlib.sha256()
    for _ in items:
        h.update(_.as_bytes())
    return SExp(h.digest())


@byte_operator
def op_equal(items):
    if len(items) == 0:
        return S_True
    return SExp(0 if any(_ != items[0] for _ in items[1:]) else 1)


@byte_operator
def op_unwrap(items):
    try:
        return SExp.from_blob(items[0].as_bytes())
    except (IndexError, ValueError):
        return S_False


@operator
def op_var(items):
    try:
        v = items[0].var_index()
        if v is None:
            return S_False
        return SExp(v)
    except (IndexError, ValueError):
        return S_False


def op_to_reduce(f_op):
    def do_f_op(form, context):
        items = [context.reduce_f(_, context) for _ in form[1:]]
        if has_unbound_values(items):
            return SExp([form[0], *items])
        return f_op(items)
    return do_f_op


def all_operators(remap, keyword_to_int):
    g = globals()
    d = {}
    for k, i in keyword_to_int.items():
        f_op = g.get("op_%s" % remap.get(k, k))
        if f_op:
            d[i] = f_op

    return d
