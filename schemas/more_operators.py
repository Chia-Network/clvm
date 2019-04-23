import hashlib

from opacity.ReduceError import ReduceError
from opacity.casts import bls12_381_generator, bls12_381_to_bytes, bls12_381_from_bytes


def op_sha256(args):
    h = hashlib.sha256()
    for _ in args:
        h.update(_.as_atom())
    return args.to(h.digest())


MASK_128 = ((1 << 128) - 1)


def truncate_int(v):
    v1 = abs(v) & MASK_128
    if v < 0:
        v1 = -v1
    return v1


def op_add(args):
    total = 0
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise ReduceError("add takes integer arguments, %s is not an int" % arg)
        total += r
    total = truncate_int(total)
    return args.to(total)


def op_subtract(args):
    if len(args) == 0:
        return args.to(0)
    sign = 1
    total = 0
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise ReduceError("add takes integer arguments, %s is not an int" % arg)
        total += sign * r
        total = truncate_int(total)
        sign = -1
    return args.to(total)


def op_multiply(args):
    v = 1
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise ReduceError("add takes integer arguments, %s is not an int" % arg)
        v = truncate_int(v * r)
    return args.to(v)


def op_unwrap(items):
    try:
        return items.from_blob(items[0].as_atom())
    except (IndexError, ValueError):
        raise ReduceError("bad stream: %s" % items[0])


def op_wrap(items):
    if len(items) != 1:
        raise ReduceError("wrap expects exactly one argument, got %d" % len(items))
    return items.to(items[0].as_bin())


def op_pubkey_for_exp(items):
    if len(items) != 1:
        raise ReduceError("op_pubkey_for_exp expects exactly one argument, got %d" % len(items))
    try:
        return items.to(bls12_381_to_bytes(bls12_381_generator * items[0].as_int()))
    except Exception as ex:
        raise ReduceError("problem in op_pubkey_for_exp: %s" % ex)


def op_point_add(items):
    if len(items) < 1:
        raise ReduceError("point_add expects at least one argument, got %d" % len(items))
    p = bls12_381_generator.infinity()
    for _ in items:
        try:
            p += bls12_381_from_bytes(_.as_atom())
        except Exception as ex:
            raise ReduceError("point_add expects blob, got %s: %s" % (_, ex))
    return items.to(bls12_381_to_bytes(p))
