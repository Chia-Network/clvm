import hashlib
import io

from blspy import G1Element

from .EvalError import EvalError
from .casts import limbs_for_int

from .costs import (
    MIN_COST,
    ADD_COST_PER_LIMB,
    MUL_COST_PER_LIMB,
    DIVMOD_COST_PER_LIMB,
    SHA256_COST,
    PUBKEY_FOR_EXP_COST,
    POINT_ADD_COST,
    CONCAT_COST_PER_BYTE,
    LOGOP_COST_PER_BYTE,
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


def args_as_ints(op_name, args):
    for arg in args.as_iter():
        if not arg.listp():
            r = arg.as_int()
            if r is not None:
                yield r
                continue
        raise EvalError("%s requires int args" % op_name, args)


def args_as_int_list(op_name, args, count):
    int_list = list(args_as_ints(op_name, args))
    if len(int_list) != count:
        plural = "s" if count != 1 else ""
        raise EvalError("%s requires %d arg%s" % (op_name, count, plural), args)
    return int_list


def op_add(args):
    total = 0
    cost = MIN_COST
    for r in args_as_ints("+", args):
        total += r
        cost += limbs_for_int(r) * ADD_COST_PER_LIMB
    return cost, args.to(total)


def op_subtract(args):
    cost = MIN_COST
    if args.nullp():
        return args.to(0)
    sign = 1
    total = 0
    for r in args_as_ints("-", args):
        total += sign * r
        sign = -1
        cost += limbs_for_int(r) * ADD_COST_PER_LIMB
    return cost, args.to(total)


def op_multiply(args):
    cost = MIN_COST
    v = 1
    for r in args_as_ints("*", args):
        cost += MUL_COST_PER_LIMB * limbs_for_int(r) * limbs_for_int(v)
        v = v * r
    return cost, args.to(v)


def op_divmod(args):
    cost = MIN_COST
    i0, i1 = args_as_int_list("divmod", args, 2)
    cost += DIVMOD_COST_PER_LIMB * (limbs_for_int(i0) + limbs_for_int(i1))
    q, r = divmod(i0, i1)
    return cost, args.to((q, r))


def op_gr(args):
    i0, i1 = args_as_int_list(">", args, 2)
    cost = ADD_COST_PER_LIMB * max(i0, i1)
    return cost, args.true if i0 > i1 else args.false


def op_gr_bytes(args):
    arg_list = list(args.as_iter())
    if len(arg_list) != 2:
        raise EvalError(">s requires 2 args", args)
    a0, a1 = arg_list
    if a0.listp() or a1.listp():
        raise EvalError(">s on list", args)
    b0 = a0.as_atom()
    b1 = a1.as_atom()
    cost = max(len(b0), len(b1))
    return cost, args.true if b0 > b1 else args.false


def op_pubkey_for_exp(args):
    (i0,) = args_as_int_list("pubkey_for_exp", args, 1)
    i0 %= 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    try:
        cost = PUBKEY_FOR_EXP_COST
        r = args.to(bytes(G1Element.generator() * i0))
        return cost, r
    except Exception as ex:
        raise EvalError("problem in op_pubkey_for_exp: %s" % ex, args)


def op_point_add(items):
    cost = MIN_COST
    p = G1Element.generator() * 0

    for _ in items.as_iter():
        try:
            p += G1Element.from_bytes(_.as_bytes())
            cost += POINT_ADD_COST
        except Exception as ex:
            raise EvalError("point_add expects blob, got %s: %s" % (_, ex), items)
    return cost, items.to(p)


def op_strlen(args):
    a0 = args.first()
    if a0.listp():
        raise EvalError("len on list", a0)
    size = len(a0.as_atom())
    cost = size
    return cost, args.to(size)


def op_substr(args):
    a0 = args.first()
    if a0.listp():
        raise EvalError("substr on list", a0)

    i1, i2 = args_as_int_list("substr", args.rest(), 2)

    s0 = a0.as_atom()
    if i2 > len(s0) or i2 < i1 or i2 < 0 or i1 < 0:
        raise EvalError("invalid indices for substr", args)
    s = s0[i1:i2]
    cost = 1
    return cost, args.to(s)


def op_concat(args):
    cost = 1
    s = io.BytesIO()
    for arg in args.as_iter():
        if arg.listp():
            raise EvalError("concat on list", arg)
        s.write(arg.as_atom())
    r = s.getvalue()
    cost += len(r) * CONCAT_COST_PER_BYTE
    return cost, args.to(r)


def op_ash(args):
    cost = MIN_COST
    i0, i1 = args_as_int_list("ash", args, 2)
    if i1 >= 0:
        r = i0 << i1
    else:
        r = i0 >> -i1
    cost += limbs_for_int(i0) * LOGOP_COST_PER_BYTE
    cost += limbs_for_int(r) * LOGOP_COST_PER_BYTE
    return cost, args.to(r)


def op_lsh(args):
    cost = MIN_COST
    i0, i1 = args_as_int_list("ash", args, 2)
    # we actually want i0 to be an *unsigned* int
    a0 = args.first().as_atom()
    i0 = int.from_bytes(a0, "big", signed=False)
    if i1 >= 0:
        r = i0 << i1
    else:
        r = i0 >> -i1
    cost += limbs_for_int(i0) * LOGOP_COST_PER_BYTE
    cost += limbs_for_int(r) * LOGOP_COST_PER_BYTE
    return cost, args.to(r)


def binop_reduction(op_name, cost, initial_value, args, op_f):
    total = initial_value
    for r in args_as_ints(op_name, args):
        total, this_cost = op_f(total, r)
        cost += this_cost
    return cost, args.to(total)


def op_logand(args):
    def binop(a, b):
        a &= b
        cost = limbs_for_int(a) * LOGOP_COST_PER_BYTE
        return a, cost

    return binop_reduction("logand", MIN_COST, -1, args, binop)


def op_logior(args):
    def binop(a, b):
        a |= b
        cost = limbs_for_int(a) * LOGOP_COST_PER_BYTE
        return a, cost

    return binop_reduction("logior", MIN_COST, 0, args, binop)


def op_logxor(args):
    def binop(a, b):
        a ^= b
        cost = limbs_for_int(a) * LOGOP_COST_PER_BYTE
        return a, cost

    return binop_reduction("logxor", MIN_COST, 0, args, binop)


def op_lognot(args):
    (i0,) = args_as_int_list("lognot", args, 1)
    r = ~i0
    limbs = limbs_for_int(r)
    cost = limbs * LOGOP_COST_PER_BYTE
    return cost, args.to(r)


def op_softfork(args):
    cost = args.first().as_int()
    if cost < 1:
        raise EvalError("cost must be > 0", args)
    return cost, args.to(0)
