import hashlib
import io

from blspy import G1Element

from .EvalError import EvalError
from .casts import limbs_for_int

from .costs import (
    ARITH_BASE_COST,
    ARITH_COST_PER_LIMB_DIVIDER,
    ARITH_COST_PER_ARG,
    LOG_BASE_COST,
    LOG_COST_PER_ARG,
    LOG_COST_PER_LIMB_DIVIDER,
    DIVMOD_BASE_COST,
    DIVMOD_COST_PER_LIMB_DIVIDER,
    DIV_BASE_COST,
    DIV_COST_PER_LIMB_DIVIDER,
    MUL_BASE_COST,
    MUL_COST_PER_OP,
    MUL_LINEAR_COST_PER_BYTE_DIVIDER,
    MUL_SQUARE_COST_PER_BYTE_DIVIDER,
    SHA256_BASE_COST,
    SHA256_COST_PER_ARG,
    SHA256_COST_PER_BYTE_DIVIDER,
    PUBKEY_BASE_COST,
    PUBKEY_COST_PER_BYTE_DIVIDER,
    POINT_ADD_BASE_COST,
    POINT_ADD_COST_PER_ARG,
    STRLEN_BASE_COST,
    STRLEN_COST_PER_BYTE_DIVIDER,
    CONCAT_BASE_COST,
    CONCAT_COST_PER_ARG,
    CONCAT_COST_PER_BYTE_DIVIDER,
    BOOL_BASE_COST,
    BOOL_COST_PER_ARG,
    LOGNOT_BASE_COST,
    LOGNOT_COST_PER_BYTE_DIVIDER,
    SHIFT_BASE_COST,
    SHIFT_COST_PER_BYTE_DIVIDER,
    CMP_BASE_COST,
    CMP_COST_PER_LIMB_DIVIDER,
    GR_BASE_COST,
    GR_COST_PER_LIMB_DIVIDER,
)


def op_sha256(args):
    cost = SHA256_BASE_COST
    arg_len = 0
    h = hashlib.sha256()
    for _ in args.as_iter():
        atom = _.atom
        if atom is None:
            raise EvalError("sha256 on list", _)
        arg_len += len(atom)
        cost += SHA256_COST_PER_ARG
        h.update(atom)
    cost += arg_len // SHA256_COST_PER_BYTE_DIVIDER
    return cost, args.to(h.digest())


def args_as_ints(op_name, args):
    for arg in args.as_iter():
        if arg.pair:
            raise EvalError("%s requires int args" % op_name, arg)
        yield (arg.as_int(), len(arg.as_atom()))


def args_as_int_list(op_name, args, count):
    int_list = list(args_as_ints(op_name, args))
    if len(int_list) != count:
        plural = "s" if count != 1 else ""
        raise EvalError("%s takes exactly %d argument%s" % (op_name, count, plural), args)
    return int_list


def args_as_bools(op_name, args):
    for arg in args.as_iter():
        v = arg.as_atom()
        if v == b"":
            yield args.false
        else:
            yield args.true


def args_as_bool_list(op_name, args, count):
    bool_list = list(args_as_bools(op_name, args))
    if len(bool_list) != count:
        plural = "s" if count != 1 else ""
        raise EvalError("%s takes exactly %d argument%s" % (op_name, count, plural), args)
    return bool_list


def op_add(args):
    total = 0
    cost = ARITH_BASE_COST
    arg_size = 0
    for r, l in args_as_ints("+", args):
        total += r
        arg_size += l
        cost += ARITH_COST_PER_ARG
    cost += arg_size // ARITH_COST_PER_LIMB_DIVIDER
    return cost, args.to(total)


def op_subtract(args):
    cost = ARITH_BASE_COST
    if args.nullp():
        return cost, args.to(0)
    sign = 1
    total = 0
    arg_size = 0
    for r, l in args_as_ints("-", args):
        total += sign * r
        sign = -1
        arg_size += l
        cost += ARITH_COST_PER_ARG
    cost += arg_size // ARITH_COST_PER_LIMB_DIVIDER
    return cost, args.to(total)


def op_multiply(args):
    cost = MUL_BASE_COST
    operands = args_as_ints("*", args)
    try:
        v, vs = next(operands)
    except StopIteration:
        return cost, args.to(1)

    for r, rs in operands:
        cost += MUL_COST_PER_OP
        cost += (rs + vs) // MUL_LINEAR_COST_PER_BYTE_DIVIDER
        cost += (rs * vs) // MUL_SQUARE_COST_PER_BYTE_DIVIDER
        v = v * r
        vs = limbs_for_int(v)
    return cost, args.to(v)


def op_divmod(args):
    cost = DIVMOD_BASE_COST
    (i0, l0), (i1, l1) = args_as_int_list("divmod", args, 2)
    if i1 == 0:
        raise EvalError("divmod with 0", args.to(i0))
    cost += (l0 + l1) // DIVMOD_COST_PER_LIMB_DIVIDER
    q, r = divmod(i0, i1)
    return cost, args.to((q, r))


def op_div(args):
    cost = DIV_BASE_COST
    (i0, l0), (i1, l1) = args_as_int_list("div", args, 2)
    if i1 == 0:
        raise EvalError("div with 0", args.to(i0))
    cost += (l0 + l1) // DIV_COST_PER_LIMB_DIVIDER
    q = i0 // i1
    return cost, args.to(q)


def op_gr(args):
    (i0, l0), (i1, l1) = args_as_int_list(">", args, 2)
    cost = GR_BASE_COST
    cost += (l0 + l1) // GR_COST_PER_LIMB_DIVIDER
    return cost, args.true if i0 > i1 else args.false


def op_gr_bytes(args):
    arg_list = list(args.as_iter())
    if len(arg_list) != 2:
        raise EvalError(">s takes exactly 2 arguments", args)
    a0, a1 = arg_list
    if a0.pair or a1.pair:
        raise EvalError(">s on list", a0 if a0.pair else a1)
    b0 = a0.as_atom()
    b1 = a1.as_atom()
    cost = CMP_BASE_COST
    cost += (len(b0) + len(b1)) // CMP_COST_PER_LIMB_DIVIDER
    return cost, args.true if b0 > b1 else args.false


def op_pubkey_for_exp(args):
    ((i0, l0),) = args_as_int_list("pubkey_for_exp", args, 1)
    i0 %= 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    try:
        r = args.to(bytes(G1Element.generator() * i0))
        cost = PUBKEY_BASE_COST
        cost += l0 // PUBKEY_COST_PER_BYTE_DIVIDER
        return cost, r
    except Exception as ex:
        raise EvalError("problem in op_pubkey_for_exp: %s" % ex, args)


def op_point_add(items):
    cost = POINT_ADD_BASE_COST
    p = G1Element.generator() * 0

    for _ in items.as_iter():
        if _.pair:
            raise EvalError("point_add on list", _)
        try:
            p += G1Element.from_bytes(_.as_atom())
            cost += POINT_ADD_COST_PER_ARG
        except Exception as ex:
            raise EvalError("point_add expects blob, got %s: %s" % (_, ex), items)
    return cost, items.to(p)


def op_strlen(args):
    if args.list_len() != 1:
        raise EvalError("strlen takes exactly 1 argument", args)
    a0 = args.first()
    if a0.pair:
        raise EvalError("strlen on list", a0)
    size = len(a0.as_atom())
    cost = STRLEN_BASE_COST + size // STRLEN_COST_PER_BYTE_DIVIDER
    return cost, args.to(size)


def op_substr(args):
    if args.list_len() != 3:
        raise EvalError("substr takes exactly 3 arguments", args)
    a0 = args.first()
    if a0.pair:
        raise EvalError("substr on list", a0)

    (i1, _), (i2, _) = args_as_int_list("substr", args.rest(), 2)

    s0 = a0.as_atom()
    if i2 > len(s0) or i2 < i1 or i2 < 0 or i1 < 0:
        raise EvalError("invalid indices for substr", args)
    s = s0[i1:i2]
    cost = 1
    return cost, args.to(s)


def op_concat(args):
    cost = CONCAT_BASE_COST
    s = io.BytesIO()
    for arg in args.as_iter():
        if arg.pair:
            raise EvalError("concat on list", arg)
        s.write(arg.as_atom())
        cost += CONCAT_COST_PER_ARG
    r = s.getvalue()
    cost += len(r) // CONCAT_COST_PER_BYTE_DIVIDER
    return cost, args.to(r)


def op_ash(args):
    (i0, l0), (i1, _) = args_as_int_list("ash", args, 2)
    if abs(i1) > 65535:
        raise EvalError("shift too large", args.to(i1))
    if i1 >= 0:
        r = i0 << i1
    else:
        r = i0 >> -i1
    cost = SHIFT_BASE_COST
    cost += (l0 + limbs_for_int(r)) // SHIFT_COST_PER_BYTE_DIVIDER
    return cost, args.to(r)


def op_lsh(args):
    (i0, l0), (i1, _) = args_as_int_list("lsh", args, 2)
    if abs(i1) > 65535:
        raise EvalError("shift too large", args.to(i1))
    # we actually want i0 to be an *unsigned* int
    a0 = args.first().as_atom()
    i0 = int.from_bytes(a0, "big", signed=False)
    if i1 >= 0:
        r = i0 << i1
    else:
        r = i0 >> -i1
    cost = SHIFT_BASE_COST
    cost += (l0 + limbs_for_int(r)) // SHIFT_COST_PER_BYTE_DIVIDER
    return cost, args.to(r)


def binop_reduction(op_name, initial_value, args, op_f):
    total = initial_value
    arg_size = 0
    cost = LOG_BASE_COST
    for r, l in args_as_ints(op_name, args):
        total = op_f(total, r)
        arg_size += l
        cost += LOG_COST_PER_ARG
    cost += arg_size // LOG_COST_PER_LIMB_DIVIDER
    return cost, args.to(total)


def op_logand(args):
    def binop(a, b):
        a &= b
        return a

    return binop_reduction("logand", -1, args, binop)


def op_logior(args):
    def binop(a, b):
        a |= b
        return a

    return binop_reduction("logior", 0, args, binop)


def op_logxor(args):
    def binop(a, b):
        a ^= b
        return a

    return binop_reduction("logxor", 0, args, binop)


def op_lognot(args):
    (i0, l0), = args_as_int_list("lognot", args, 1)
    cost = LOGNOT_BASE_COST + l0 // LOGNOT_COST_PER_BYTE_DIVIDER
    return cost, args.to(~i0)


def op_not(args):
    (i0,) = args_as_bool_list("not", args, 1)
    if i0.as_atom() == b"":
        r = args.true
    else:
        r = args.false
    cost = BOOL_BASE_COST + BOOL_COST_PER_ARG
    return cost, args.to(r)


def op_any(args):
    items = list(args_as_bools("any", args))
    cost = BOOL_BASE_COST + len(items) * BOOL_COST_PER_ARG
    r = args.false
    for v in items:
        if v.as_atom() != b"":
            r = args.true
            break
    return cost, args.to(r)


def op_all(args):
    items = list(args_as_bools("all", args))
    cost = BOOL_BASE_COST + len(items) * BOOL_COST_PER_ARG
    r = args.true
    for v in items:
        if v.as_atom() == b"":
            r = args.false
            break
    return cost, args.to(r)


def op_softfork(args):
    if args.list_len() < 1:
        raise EvalError("softfork takes at least 1 argument", args)
    a = args.first()
    if a.pair:
        raise EvalError("softfork requires int args", a)
    cost = a.as_int()
    if cost < 1:
        raise EvalError("cost must be > 0", args)
    return cost, args.to(0)
