from .EvalError import EvalError
from .SExp import SExp

from .costs import (
    IF_COST,
    CONS_COST,
    FIRST_COST,
    REST_COST,
    LISTP_COST,
    EQ_BASE_COST,
    EQ_COST_PER_BYTE,
)


def op_if(args: SExp):
    if args.list_len() != 3:
        raise EvalError("i takes exactly 3 arguments", args)
    r = args.rest()
    if args.first().nullp():
        return IF_COST, r.rest().first()
    return IF_COST, r.first()


def op_cons(args: SExp):
    if args.list_len() != 2:
        raise EvalError("c takes exactly 2 arguments", args)
    return CONS_COST, args.first().cons(args.rest().first())


def op_first(args: SExp):
    if args.list_len() != 1:
        raise EvalError("f takes exactly 1 argument", args)
    return FIRST_COST, args.first().first()


def op_rest(args: SExp):
    if args.list_len() != 1:
        raise EvalError("r takes exactly 1 argument", args)
    return REST_COST, args.first().rest()


def op_listp(args: SExp):
    if args.list_len() != 1:
        raise EvalError("l takes exactly 1 argument", args)
    return LISTP_COST, args.true if args.first().listp() else args.false


def op_raise(args: SExp):
    raise EvalError("clvm raise", args)


def op_eq(args: SExp):
    if args.list_len() != 2:
        raise EvalError("= takes exactly 2 arguments", args)
    a0 = args.first()
    a1 = args.rest().first()
    if a0.pair or a1.pair:
        raise EvalError("= on list", a0 if a0.pair else a1)
    b0 = a0.as_atom()
    b1 = a1.as_atom()
    cost = EQ_BASE_COST
    cost += (len(b0) + len(b1)) * EQ_COST_PER_BYTE
    return cost, (args.true if b0 == b1 else args.false)
