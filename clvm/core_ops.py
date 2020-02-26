from .EvalError import EvalError


def op_if(args):
    r = args.rest()
    if args.first().nullp():
        return r.rest().first()
    return r.first()


def op_cons(args):
    return args.first().cons(args.rest().first())


def op_first(args):
    return args.first().first()


def op_rest(args):
    return args.first().rest()


def op_listp(args):
    return args.true if args.first().listp() else args.false


def op_raise(args):
    raise EvalError("clvm raise", args)


def op_eq(args):
    a0 = args.first()
    a1 = args.rest().first()
    if a0.listp() or a1.listp():
        raise EvalError("= on list", args)
    return args.true if a0.as_atom() == a1.as_atom() else args.false
