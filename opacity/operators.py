import hashlib

from .casts import bls12_381_from_bytes, bls12_381_to_bytes
from .ecdsa.bls12_381 import bls12_381_generator

from .SExp import SExp


S_False = SExp(0)
S_True = SExp(1)


MASK_128 = ((1 << 128) - 1)


def truncate_int(v):
    v1 = abs(v) & MASK_128
    if v < 0:
        v1 = -v1
    return v1


def has_unbound_values(items):
    return any(not _.is_bytes() for _ in items)


def op_and(items):
    return S_False if S_False in items else S_True


def op_pubkey_for_exp(items):
    def blob_for_item(_):
        try:
            return bls12_381_to_bytes(bls12_381_generator * _.as_int())
        except Exception as ex:
            return b''

    if len(items) < 1:
        return S_False
    return SExp(blob_for_item(items[0]))


def op_point_add(items):
    if len(items) < 1:
        return S_False
    p = bls12_381_from_bytes(items[0].as_bytes())
    for _ in items[1:]:
        p += bls12_381_from_bytes(_.as_bytes())
    return SExp(bls12_381_to_bytes(p))


def op_add(items):
    return SExp(sum(_.as_int() for _ in items))


def op_multiply(items):
    v = 1
    for _ in items:
        v *= _.as_int()
        v = truncate_int(v)
    return SExp(v)


def op_subtract(items):
    if len(items) == 0:
        return SExp(0)
    v = items[0].as_int()
    for _ in items[1:]:
        v -= _.as_int()
        v = truncate_int(v)
    return SExp(v)


def op_sha256(items):
    h = hashlib.sha256()
    for _ in items:
        h.update(_.as_bytes())
    return SExp(h.digest())


def op_equal(items):
    if len(items) == 0:
        return S_True
    return SExp(0 if any(_ != items[0] for _ in items[1:]) else 1)


def op_unwrap(items):
    try:
        return SExp.from_blob(items[0].as_bytes())
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
            d[i] = op_to_reduce(f_op)

    return d
