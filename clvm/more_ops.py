import hashlib
import io
import typing

from chia_rs import G1Element, PrivateKey

from .EvalError import EvalError
from .casts import limbs_for_int
from .SExp import SExp

from .costs import (
    ARITH_BASE_COST,
    ARITH_COST_PER_BYTE,
    ARITH_COST_PER_ARG,
    LOG_BASE_COST,
    LOG_COST_PER_ARG,
    LOG_COST_PER_BYTE,
    DIVMOD_BASE_COST,
    DIVMOD_COST_PER_BYTE,
    DIV_BASE_COST,
    DIV_COST_PER_BYTE,
    MUL_BASE_COST,
    MUL_COST_PER_OP,
    MUL_LINEAR_COST_PER_BYTE,
    MUL_SQUARE_COST_PER_BYTE_DIVIDER,
    SHA256_BASE_COST,
    SHA256_COST_PER_ARG,
    SHA256_COST_PER_BYTE,
    PUBKEY_BASE_COST,
    PUBKEY_COST_PER_BYTE,
    POINT_ADD_BASE_COST,
    POINT_ADD_COST_PER_ARG,
    STRLEN_BASE_COST,
    STRLEN_COST_PER_BYTE,
    CONCAT_BASE_COST,
    CONCAT_COST_PER_ARG,
    CONCAT_COST_PER_BYTE,
    BOOL_BASE_COST,
    BOOL_COST_PER_ARG,
    LOGNOT_BASE_COST,
    LOGNOT_COST_PER_BYTE,
    LSHIFT_BASE_COST,
    LSHIFT_COST_PER_BYTE,
    ASHIFT_BASE_COST,
    ASHIFT_COST_PER_BYTE,
    GRS_BASE_COST,
    GRS_COST_PER_BYTE,
    GR_BASE_COST,
    GR_COST_PER_BYTE,
    MALLOC_COST_PER_BYTE,
)


_T_SExp = typing.TypeVar("_T_SExp", bound=SExp)


def malloc_cost(cost: int, atom: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    if atom.atom is None:
        raise ValueError("Atom must have a non-None atom attribute")
    return cost + len(atom.atom) * MALLOC_COST_PER_BYTE, atom


def op_sha256(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
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
    cost += arg_len * SHA256_COST_PER_BYTE
    return malloc_cost(cost, args.to(h.digest()))


def args_as_ints(op_name: str, args: SExp) -> typing.Iterator[typing.Tuple[int, int]]:
    for arg in args.as_iter():
        if arg.atom is None:
            raise EvalError("%s requires int args" % op_name, arg)
        yield (arg.as_int(), len(arg.atom))


def args_as_int32(op_name: str, args: SExp) -> typing.Iterator[int]:
    for arg in args.as_iter():
        if arg.atom is None:
            raise EvalError("%s requires int32 args" % op_name, arg)
        if len(arg.atom) > 4:
            raise EvalError(
                "%s requires int32 args (with no leading zeros)" % op_name, arg
            )
        yield arg.as_int()


def args_as_int_list(
    op_name: str, args: SExp, count: int
) -> typing.List[typing.Tuple[int, int]]:
    int_list = list(args_as_ints(op_name, args))
    if len(int_list) != count:
        plural = "s" if count != 1 else ""
        raise EvalError(
            "%s takes exactly %d argument%s" % (op_name, count, plural), args
        )
    return int_list


def args_as_bools(op_name: str, args: SExp) -> typing.Iterator[SExp]:
    for arg in args.as_iter():
        v = arg.as_atom()
        if v == b"":
            yield args.false
        else:
            yield args.true


def args_as_bool_list(op_name: str, args: SExp, count: int) -> typing.List[SExp]:
    bool_list = list(args_as_bools(op_name, args))
    if len(bool_list) != count:
        plural = "s" if count != 1 else ""
        raise EvalError(
            "%s takes exactly %d argument%s" % (op_name, count, plural), args
        )
    return bool_list


def op_add(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    total = 0
    cost = ARITH_BASE_COST
    arg_size = 0
    for r, arg_len in args_as_ints("+", args):
        total += r
        arg_size += arg_len
        cost += ARITH_COST_PER_ARG
    cost += arg_size * ARITH_COST_PER_BYTE
    return malloc_cost(cost, args.to(total))


def op_subtract(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    cost = ARITH_BASE_COST
    if args.nullp():
        return malloc_cost(cost, args.to(0))
    sign = 1
    total = 0
    arg_size = 0
    for r, arg_len in args_as_ints("-", args):
        total += sign * r
        sign = -1
        arg_size += arg_len
        cost += ARITH_COST_PER_ARG
    cost += arg_size * ARITH_COST_PER_BYTE
    return malloc_cost(cost, args.to(total))


def op_multiply(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    cost = MUL_BASE_COST
    operands = args_as_ints("*", args)
    try:
        v, vs = next(operands)
    except StopIteration:
        return malloc_cost(cost, args.to(1))

    for r, rs in operands:
        cost += MUL_COST_PER_OP
        cost += (rs + vs) * MUL_LINEAR_COST_PER_BYTE
        cost += (rs * vs) // MUL_SQUARE_COST_PER_BYTE_DIVIDER
        v = v * r
        vs = limbs_for_int(v)
    return malloc_cost(cost, args.to(v))


def op_divmod(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    cost = DIVMOD_BASE_COST
    (i0, l0), (i1, l1) = args_as_int_list("divmod", args, 2)
    if i1 == 0:
        raise EvalError("divmod with 0", args.to(i0))
    cost += (l0 + l1) * DIVMOD_COST_PER_BYTE
    q, r = divmod(i0, i1)
    # since q and r are integers, the atoms will be non-None
    q1_atom: bytes = args.to(q).atom  # type: ignore[assignment]
    r1_atom: bytes = args.to(r).atom  # type: ignore[assignment]
    cost += (len(q1_atom) + len(r1_atom)) * MALLOC_COST_PER_BYTE
    return cost, args.to((q, r))


def op_div(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    cost = DIV_BASE_COST
    (i0, l0), (i1, l1) = args_as_int_list("/", args, 2)
    if i1 == 0:
        raise EvalError("div with 0", args.to(i0))

    if i0 < 0 or i1 < 0:
        raise EvalError("div operator with negative operands is deprecated", args)

    cost += (l0 + l1) * DIV_COST_PER_BYTE
    q, r = divmod(i0, i1)

    return malloc_cost(cost, args.to(q))


def op_gr(args: SExp) -> typing.Tuple[int, SExp]:
    (i0, l0), (i1, l1) = args_as_int_list(">", args, 2)
    cost = GR_BASE_COST
    cost += (l0 + l1) * GR_COST_PER_BYTE
    return cost, args.true if i0 > i1 else args.false


def op_gr_bytes(args: SExp) -> typing.Tuple[int, SExp]:
    arg_list = list(args.as_iter())
    if len(arg_list) != 2:
        raise EvalError(">s takes exactly 2 arguments", args)
    a0, a1 = arg_list
    if a0.pair or a1.pair:
        raise EvalError(">s on list", a0 if a0.pair else a1)
    b0 = a0.as_atom()
    b1 = a1.as_atom()
    cost = GRS_BASE_COST
    if b0 is None or b1 is None:
        raise TypeError("Internal error, both operands must not be None")
    cost += (len(b0) + len(b1)) * GRS_COST_PER_BYTE
    return cost, args.true if b0 > b1 else args.false


def op_pubkey_for_exp(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    ((i0, l0),) = args_as_int_list("pubkey_for_exp", args, 1)
    i0 %= 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    exponent = PrivateKey.from_bytes(i0.to_bytes(32, "big"))
    try:
        r = args.to(bytes(exponent.get_g1()))
        cost = PUBKEY_BASE_COST
        cost += l0 * PUBKEY_COST_PER_BYTE
        return malloc_cost(cost, r)
    except Exception as ex:
        raise EvalError("problem in op_pubkey_for_exp: %s" % ex, args)


def op_point_add(items: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    cost = POINT_ADD_BASE_COST
    p = G1Element()

    for _ in items.as_iter():
        if _.pair:
            raise EvalError("point_add on list", _)
        try:
            atom = _.as_atom()
            assert atom is not None
            p += G1Element.from_bytes(atom)
            cost += POINT_ADD_COST_PER_ARG
        except Exception as ex:
            raise EvalError("point_add expects blob, got %s: %s" % (_, ex), items)
    return malloc_cost(cost, items.to(p))


def op_strlen(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    if args.list_len() != 1:
        raise EvalError("strlen takes exactly 1 argument", args)
    a0 = args.first()
    if a0.pair:
        raise EvalError("strlen on list", a0)
    assert a0.atom is not None
    size = len(a0.atom)
    cost = STRLEN_BASE_COST + size * STRLEN_COST_PER_BYTE
    return malloc_cost(cost, args.to(size))


def op_substr(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    arg_count = args.list_len()
    if arg_count not in (2, 3):
        raise EvalError("substr takes exactly 2 or 3 arguments", args)
    a0 = args.first()
    if a0.pair:
        raise EvalError("substr on list", a0)

    s0 = a0.as_atom()
    assert s0 is not None

    if arg_count == 2:
        (i1,) = list(args_as_int32("substr", args.rest()))
        i2 = len(s0)
    else:
        i1, i2 = list(args_as_int32("substr", args.rest()))

    if i2 > len(s0) or i2 < i1 or i2 < 0 or i1 < 0:
        raise EvalError("invalid indices for substr", args)
    s = s0[i1:i2]
    cost = 1
    return cost, args.to(s)


def op_concat(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    cost = CONCAT_BASE_COST
    s = io.BytesIO()
    for arg in args.as_iter():
        if arg.pair:
            raise EvalError("concat on list", arg)
        assert arg.atom is not None
        s.write(arg.atom)
        cost += CONCAT_COST_PER_ARG
    r = s.getvalue()
    cost += len(r) * CONCAT_COST_PER_BYTE
    return malloc_cost(cost, args.to(r))


def op_ash(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    (i0, l0), (i1, l1) = args_as_int_list("ash", args, 2)
    if l1 > 4:
        raise EvalError(
            "ash requires int32 args (with no leading zeros)", args.rest().first()
        )
    if abs(i1) > 65535:
        raise EvalError("shift too large", args.to(i1))
    if i1 >= 0:
        r = i0 << i1
    else:
        r = i0 >> -i1
    cost = ASHIFT_BASE_COST
    cost += (l0 + limbs_for_int(r)) * ASHIFT_COST_PER_BYTE
    return malloc_cost(cost, args.to(r))


def op_lsh(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    (i0, l0), (i1, l1) = args_as_int_list("lsh", args, 2)
    if l1 > 4:
        raise EvalError(
            "lsh requires int32 args (with no leading zeros)", args.rest().first()
        )
    if abs(i1) > 65535:
        raise EvalError("shift too large", args.to(i1))
    # we actually want i0 to be an *unsigned* int
    a0 = args.first().as_atom()
    assert a0 is not None
    i0 = int.from_bytes(a0, "big", signed=False)
    if i1 >= 0:
        r = i0 << i1
    else:
        r = i0 >> -i1
    cost = LSHIFT_BASE_COST
    cost += (l0 + limbs_for_int(r)) * LSHIFT_COST_PER_BYTE
    return malloc_cost(cost, args.to(r))


def binop_reduction(
    op_name: str,
    initial_value: int,
    args: _T_SExp,
    op_f: typing.Callable[[int, int], int],
) -> typing.Tuple[int, _T_SExp]:
    total = initial_value
    arg_size = 0
    cost = LOG_BASE_COST
    for r, arg_len in args_as_ints(op_name, args):
        total = op_f(total, r)
        arg_size += arg_len
        cost += LOG_COST_PER_ARG
    cost += arg_size * LOG_COST_PER_BYTE
    return malloc_cost(cost, args.to(total))


def op_logand(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    def binop(a: int, b: int) -> int:
        a &= b
        return a

    return binop_reduction("logand", -1, args, binop)


def op_logior(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    def binop(a: int, b: int) -> int:
        a |= b
        return a

    return binop_reduction("logior", 0, args, binop)


def op_logxor(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    def binop(a: int, b: int) -> int:
        a ^= b
        return a

    return binop_reduction("logxor", 0, args, binop)


def op_lognot(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    ((i0, l0),) = args_as_int_list("lognot", args, 1)
    cost = LOGNOT_BASE_COST + l0 * LOGNOT_COST_PER_BYTE
    return malloc_cost(cost, args.to(~i0))


def op_not(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    (i0,) = args_as_bool_list("not", args, 1)
    if i0.as_atom() == b"":
        r = args.true
    else:
        r = args.false
    cost = BOOL_BASE_COST
    return cost, args.to(r)


def op_any(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    items = list(args_as_bools("any", args))
    cost = BOOL_BASE_COST + len(items) * BOOL_COST_PER_ARG
    r = args.false
    for v in items:
        if v.as_atom() != b"":
            r = args.true
            break
    return cost, args.to(r)


def op_all(args: _T_SExp) -> typing.Tuple[int, _T_SExp]:
    items = list(args_as_bools("all", args))
    cost = BOOL_BASE_COST + len(items) * BOOL_COST_PER_ARG
    r = args.true
    for v in items:
        if v.as_atom() == b"":
            r = args.false
            break
    return cost, args.to(r)


def op_softfork(args: SExp) -> typing.Tuple[int, SExp]:
    if args.list_len() < 1:
        raise EvalError("softfork takes at least 1 argument", args)
    a = args.first()
    if a.pair:
        raise EvalError("softfork requires int args", a)
    cost = a.as_int()
    if cost < 1:
        raise EvalError("cost must be > 0", args)
    return cost, args.false
