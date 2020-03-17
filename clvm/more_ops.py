import hashlib

from .EvalError import EvalError
from .casts import (
    bls12_381_generator, bls12_381_to_bytes, bls12_381_from_bytes,
    limbs_for_int
)


from .costs import (
    MIN_COST,
    ADD_COST_PER_LIMB,
    MUL_COST_PER_LIMB,
    SHA256_COST,
    PUBKEY_FOR_EXP_COST,
    POINT_ADD_COST,
)


def op_sha256(args):
    cost = SHA256_COST
    h = hashlib.sha256()
    for _ in args.as_iter():
        atom = _.as_atom()
        cost += len(atom)
        h.update(atom)
    return cost, args.to(h.digest())


def sha256tree_with_cost(v):
    if v.listp():
        cl, left = sha256tree_with_cost(v.first())
        cr, right = sha256tree_with_cost(v.rest())
        s = b"\2" + left + right
        cost = cl + cr + SHA256_COST
    else:
        atom = v.as_atom()
        s = b"\1" + atom
        cost = len(atom) + SHA256_COST
    return cost, hashlib.sha256(s).digest()


def op_sha256tree(args):
    if args.nullp() or not args.rest().nullp():
        raise EvalError("op_sha256tree expects exactly one argument", args)
    cost, r = sha256tree_with_cost(args.first())
    return cost, args.to(r)


MASK_128 = ((1 << 128) - 1)


def truncate_int(v):
    v1 = abs(v) & MASK_128
    if v < 0:
        v1 = -v1
    return v1


def op_add(args):
    total = 0
    cost = MIN_COST
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise EvalError("+ takes integer arguments", args)
        total += r
        total = truncate_int(total)
        cost += limbs_for_int(r) * ADD_COST_PER_LIMB
    return cost, args.to(total)


def op_subtract(args):
    cost = MIN_COST
    if args.nullp():
        return args.to(0)
    sign = 1
    total = 0
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise EvalError("- takes integer arguments", args)
        total += sign * r
        total = truncate_int(total)
        sign = -1
        cost += limbs_for_int(r) * ADD_COST_PER_LIMB
    return cost, args.to(total)


def op_multiply(args):
    cost = MIN_COST
    v = 1
    for arg in args.as_iter():
        r = arg.as_int()
        if r is None:
            raise EvalError("* takes integer arguments", args)
        cost += MUL_COST_PER_LIMB * limbs_for_int(r) * limbs_for_int(v)
        v = truncate_int(v * r)
    return cost, args.to(v)


def op_gr(args):
    a0 = args.first()
    a1 = args.rest().first()
    if a0.listp() or a1.listp():
        raise EvalError("> on list", args)
    i0 = a0.as_int()
    i1 = a1.as_int()
    cost = ADD_COST_PER_LIMB * max(i0, i1)
    return cost, args.true if i0 > i1 else args.false


def op_gr_bytes(args):
    a0 = args.first()
    a1 = args.rest().first()
    if a0.listp() or a1.listp():
        raise EvalError("> on list", args)
    b0 = a0.as_atom()
    b1 = a1.as_atom()
    cost = max(len(b0), len(b1))
    return cost, args.true if b0 > b1 else args.false


def op_pubkey_for_exp(items):
    if items.nullp() or not items.rest().nullp():
        raise EvalError("op_pubkey_for_exp expects exactly one argument", items)
    try:
        cost = PUBKEY_FOR_EXP_COST
        r = items.to(bls12_381_to_bytes(bls12_381_generator * items.first().as_int()))
        return cost, r
    except Exception as ex:
        raise EvalError("problem in op_pubkey_for_exp: %s" % ex, items)


def op_point_add(items):
    cost = MIN_COST
    p = bls12_381_generator.infinity()
    for _ in items.as_iter():
        try:
            p += bls12_381_from_bytes(_.as_bytes())
            cost += POINT_ADD_COST
        except Exception as ex:
            raise EvalError("point_add expects blob, got %s: %s" % (_, ex), items)
    return cost, items.to(bls12_381_to_bytes(p))
