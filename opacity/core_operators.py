from clvm.EvalError import EvalError

# s-expression operators


def op_cons(args):
    if len(args) == 2:
        return args[0].to([args[0]] + list(args[1]))
    raise EvalError("cons must take 2 args, got %d" % len(args))


def op_first(args):
    if len(args) == 1 and args[0].listp():
        return args[0].first()
    raise EvalError("first takes 1 argument, which must be a pair", args)


def op_rest(args):
    if len(args) == 1 and args[0].listp():
        return args[0].rest()
    raise EvalError("rest takes 1 argument, which must be a pair", args)


def op_type(args):
    if len(args) == 1:
        return args[0].to(args[0].type_index())
    raise EvalError("type takes exactly one parameter", args)


def op_var(args):
    if len(args) == 1 and args[0].is_var():
        return args[0].to(args[0].var_index())
    raise EvalError("type takes exactly one parameter, which must be a var", args)


def op_is_null(args):
    if len(args) == 1:
        return args[0].to(args[0].listp() and args[0].nullp())
    raise EvalError("is_null takes exactly one parameter", args)


def op_get(args):
    if len(args) != 2:
        raise EvalError("get takes exactly 2 parameters", args)
    item, index = args[0], args[1]
    if not item.listp():
        raise EvalError("get got non-list", item)
    if not index.is_bytes():
        raise EvalError("get bad index type: %s" % index)
    if 0 <= index.as_int() < len(item):
        return args[0].to(item[index.as_int()])
    raise EvalError("get bad index %d" % index.as_int())


# fail


def op_raise(args):
    raise EvalError("raise", args)


# logical operators

def op_equal(args):
    a0 = args.first()
    a1 = args.rest().first()
    if a0.listp() or a1.listp():
        raise EvalError("= on list", args)
    r = args.true if a0.as_atom() == a1.as_atom() else args.false
    return r
