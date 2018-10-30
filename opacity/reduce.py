import hashlib

from .casts import bls12_381_from_bytes, bls12_381_to_bytes
from .ecdsa.bls12_381 import bls12_381_generator
from .keywords import KEYWORD_TO_INT

from .SExp import SExp


S_False = SExp(0)
S_True = SExp(1)


def has_unbound_values(items):
    return any(not _.is_bytes() for _ in items)


def do_implicit_and(form, bindings, reduce_f):
    items = [reduce_f(_, bindings, reduce_f) for _ in form]
    if S_False in items:
        return S_False
    items = [_ for _ in items if not _.is_bytes()]
    if has_unbound_values(items):
        return SExp(items)
    return S_True if all(_ != S_False for _ in items) else S_False


def op_pubkey_for_exp(items):
    def blob_for_item(_):
        try:
            return bls12_381_to_bytes(bls12_381_generator * _.as_int())
        except Exception as ex:
            return b''

    if len(items) < 1:
        return SExp(0)
    return SExp(blob_for_item(items[0]))


def op_point_add(items):
    p = bls12_381_from_bytes(items[0].as_bytes())
    for _ in items[1:]:
        p += bls12_381_from_bytes(_.as_bytes())
    return SExp(bls12_381_to_bytes(p))


def op_add(items):
    return SExp(sum(_.as_int() for _ in items) & ((1 << 128) - 1))


def op_sha256(items):
    h = hashlib.sha256()
    for _ in items:
        h.update(_.as_bytes())
    return SExp(h.digest())


def op_equal(items):
    if len(items) == 0:
        return SExp(1)
    return SExp(0 if any(_ != items[0] for _ in items[1:]) else 1)


def do_choose1(form, bindings, reduce_f):
    if len(form) < 2:
        return S_False
    choice = reduce_f(form[1], bindings, reduce_f)
    if has_unbound_values([choice]):
        return form
    choice = choice.as_int()
    choices = form[2:]
    if 0 <= choice < len(choices):
        chosen_form = choices[choice]
        return reduce_f(chosen_form, bindings, reduce_f)
    return S_False


def do_reduce(form, bindings, reduce_f):
    items = [reduce_f(_, bindings, reduce_f) for _ in form[1:]]
    new_form = SExp.from_blob(items[0].as_bytes())
    new_bindings = SExp.from_blob(items[1].as_bytes())
    return reduce_f(new_form, new_bindings, reduce_f)


def do_recursive_reduce(form, bindings, reduce_f):
    return SExp(form.as_list()[:1] + [reduce_f(_, bindings, reduce_f) for _ in form[1:]])


def op_to_reduce(f_op):
    def do_f_op(form, bindings, reduce_f):
        items = [reduce_f(_, bindings, reduce_f) for _ in form[1:]]
        if has_unbound_values(items):
            return SExp([form[0], *items])
        return f_op(items)
    return do_f_op


def build_reduce_lookup(remap, keyword_to_int):
    g = globals()
    d = dict()
    for k, i in keyword_to_int.items():
        f = None
        if k in remap:
            k = remap[k]
        if f is None:
            f = g.get("do_%s" % k)
        if f is None:
            f_op = g.get("op_%s" % k)
            if f_op:
                f = op_to_reduce(f_op)
        if f is None:
            f = do_recursive_reduce
        if f:
            d[i] = f

    return d


REDUCE_LOOKUP = build_reduce_lookup({"+": "add"}, KEYWORD_TO_INT)


def reduce(form: SExp, bindings: SExp, reduce_f=None):
    # a lazy trick to help tests
    bindings = SExp(bindings)

    reduce_f = reduce_f or reduce

    if form.is_var():
        index = form.var_index()
        if 0 <= index < len(bindings.as_list() or []):
            return bindings.as_list()[index]
        return form

    if form.is_list():
        if len(form) > 0:
            if form[0].is_list():
                return do_implicit_and(form, bindings, reduce_f)
            operator = form[0].as_int()
            f = REDUCE_LOOKUP.get(form[0].as_int(), do_implicit_and)
            if f:
                return f(form, bindings, reduce_f)

            return f(form, bindings, reduce_f)
        return SExp(0)

    return form
