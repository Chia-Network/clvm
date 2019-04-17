from .ReduceError import ReduceError

# s-expression operators


def op_cons(args):
    if len(args) == 2:
        return args[0].__class__([args[0]] + list(args[1]))
    raise ReduceError("cons must take 2 args, got %d" % len(args))


def op_first(args):
    if len(args) == 1 and args[0].item and args[0].type == args[0].ATOM_TYPES.PAIR:
        return args[0].first()
    raise ReduceError("first takes 1 argument, which must be a pair")


def op_rest(args):
    if len(args) == 1 and args[0].item and args[0].type == args[0].ATOM_TYPES.PAIR:
        return args[0].rest()
    raise ReduceError("rest takes 1 argument, which must be a pair")


def op_type(args):
    if len(args) == 1:
        return args[0].__class__(args[0].type - 1)
    raise ReduceError("type takes exactly one parameter")


def op_var(args):
    if len(args) == 1 and args[0].type == args[0].ATOM_TYPES.VAR:
        return args[0].__class__(args[0].var_index())
    raise ReduceError("type takes exactly one parameter, which must be a var")


def op_is_null(args):
    if len(args) == 1:
        return args[0].__class__(args[0].listp() and args[0].nullp())
    raise ReduceError("is_null takes exactly one parameter, got %d" % len(args))


def op_get(args):
    if len(args) != 2:
        raise ReduceError("get takes exactly 2 parameters, got %d" % len(args))
    item, index = args[0], args[1]
    if not item.listp():
        raise ReduceError("get got non-list: %s" % item)
    if not index.is_bytes():
        raise ReduceError("get bad index type: %s" % index)
    if 0 <= index.as_int() < len(item):
        return args[0].__class__(item[index.as_int()])
    raise ReduceError("get bad index %d" % index.as_int())


# fail


def op_raise(args):
    raise ReduceError(args)


# logical operators


def op_equal(args):
    if len(args) != 2:
        raise ReduceError("equal requires 2 arguments, got %d" % len(args))
    a0, a1 = args
    if a0.type != a1.type:
        return a0.false
    if a0.type == a0.ATOM_TYPES.PAIR:
        return a0.false
    if a0.type == a0.ATOM_TYPES.VAR:
        return a0.__class__(a0.var_index() == a1.var_index())
    return a0.__class__(a0.as_bytes() == a1.as_bytes())
