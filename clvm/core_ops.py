from .EvalError import EvalError

from .costs import (
    IF_COST,
    CONS_COST,
    FIRST_COST,
    REST_COST,
    LISTP_COST,
)


def op_if(args):
    r = args.rest()
    if args.first().nullp():
        return IF_COST, r.rest().first()
    return IF_COST, r.first()


def op_cons(args):
    return CONS_COST, args.first().cons(args.rest().first())


def op_first(args):
    return FIRST_COST, args.first().first()


def op_rest(args):
    return REST_COST, args.first().rest()


def op_listp(args):
    return LISTP_COST, args.true if args.first().listp() else args.false


def op_raise(args):
    raise EvalError("clvm raise", args)


def op_eq(args):
    a0 = args.first()
    a1 = args.rest().first()
    if a0.listp() or a1.listp():
        raise EvalError("= on list", args)
    b0 = a0.as_atom()
    b1 = a1.as_atom()
    cost = len(b0) + len(b1)
    return cost, (args.true if b0 == b1 else args.false)
