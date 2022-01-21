from typing import Tuple

from .CLVMObject import CLVMObject
from .EvalError import EvalError

from .costs import (
    ARITH_BASE_COST,
    ARITH_COST_PER_BYTE,
    ARITH_COST_PER_ARG,
    MUL_BASE_COST,
    MUL_COST_PER_OP,
    MUL_LINEAR_COST_PER_BYTE,
    MUL_SQUARE_COST_PER_BYTE_DIVIDER,
    CONCAT_BASE_COST,
    CONCAT_COST_PER_ARG,
    CONCAT_COST_PER_BYTE,
)


def handle_unknown_op_strict(op, arguments, _max_cost=None):
    raise EvalError("unimplemented operator", arguments.to(op))


def args_len(op_name, args):
    for arg in args.as_iter():
        if arg.pair:
            raise EvalError("%s requires int args" % op_name, arg)
        yield len(arg.as_atom())


# unknown ops are reserved if they start with 0xffff
# otherwise, unknown ops are no-ops, but they have costs. The cost is computed
# like this:

# byte index (reverse):
# | 4 | 3 | 2 | 1 | 0          |
# +---+---+---+---+------------+
# | multiplier    |XX | XXXXXX |
# +---+---+---+---+---+--------+
#  ^               ^    ^
#  |               |    + 6 bits ignored when computing cost
# cost_multiplier  |
#                  + 2 bits
#                    cost_function

# 1 is always added to the multiplier before using it to multiply the cost, this
# is since cost may not be 0.

# cost_function is 2 bits and defines how cost is computed based on arguments:
# 0: constant, cost is 1 * (multiplier + 1)
# 1: computed like operator add, multiplied by (multiplier + 1)
# 2: computed like operator mul, multiplied by (multiplier + 1)
# 3: computed like operator concat, multiplied by (multiplier + 1)

# this means that unknown ops where cost_function is 1, 2, or 3, may still be
# fatal errors if the arguments passed are not atoms.


def handle_unknown_op_softfork_ready(
    op: bytes, args: CLVMObject, max_cost: int
) -> Tuple[int, CLVMObject]:
    # any opcode starting with ffff is reserved (i.e. fatal error)
    # opcodes are not allowed to be empty
    if len(op) == 0 or op[:2] == b"\xff\xff":
        raise EvalError("reserved operator", args.to(op))

    # all other unknown opcodes are no-ops
    # the cost of the no-ops is determined by the opcode number, except the
    # 6 least significant bits.

    cost_function = (op[-1] & 0b11000000) >> 6
    # the multiplier cannot be 0. it starts at 1

    if len(op) > 5:
        raise EvalError("invalid operator", args.to(op))

    cost_multiplier = int.from_bytes(op[:-1], "big", signed=False) + 1

    # 0 = constant
    # 1 = like op_add/op_sub
    # 2 = like op_multiply
    # 3 = like op_concat
    if cost_function == 0:
        cost = 1
    elif cost_function == 1:
        # like op_add
        cost = ARITH_BASE_COST
        arg_size = 0
        for length in args_len("unknown op", args):
            arg_size += length
            cost += ARITH_COST_PER_ARG
        cost += arg_size * ARITH_COST_PER_BYTE
    elif cost_function == 2:
        # like op_multiply
        cost = MUL_BASE_COST
        operands = args_len("unknown op", args)
        try:
            vs = next(operands)
            for rs in operands:
                cost += MUL_COST_PER_OP
                cost += (rs + vs) * MUL_LINEAR_COST_PER_BYTE
                cost += (rs * vs) // MUL_SQUARE_COST_PER_BYTE_DIVIDER
                # this is an estimate, since we don't want to actually multiply the
                # values
                vs += rs
        except StopIteration:
            pass

    elif cost_function == 3:
        # like concat
        cost = CONCAT_BASE_COST
        length = 0
        for arg in args.as_iter():
            if arg.pair:
                raise EvalError("unknown op on list", arg)
            cost += CONCAT_COST_PER_ARG
            length += len(arg.atom)
        cost += length * CONCAT_COST_PER_BYTE

    cost *= cost_multiplier
    if cost >= 2 ** 32:
        raise EvalError("invalid operator", args.to(op))

    return (cost, args.to(b""))
