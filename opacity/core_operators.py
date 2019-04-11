from .ReduceError import ReduceError
from .SExp import SExp, ATOM_TYPES


S_False = SExp(0)
S_True = SExp(1)


CORE_KEYWORDS = "quote cons first rest type var env_raw is_null raise equal get_raw".split()

# s-expression operators


def op_cons(args):
    if len(args) == 2:
        return SExp([args[0]] + list(args[1]))
    raise ReduceError("cons must take 2 args, got %d" % len(args))


def op_first(args):
    if len(args) == 1 and args[0].item and args[0].type == ATOM_TYPES.PAIR:
        return SExp(args[0].item[0])
    raise ReduceError("first takes 1 argument, which must be a pair")


def op_rest(args):
    if len(args) == 1 and args[0].item and args[0].type == ATOM_TYPES.PAIR:
        return SExp(args[0].item[1])
    raise ReduceError("rest takes 1 argument, which must be a pair")


def op_type(args):
    if len(args) == 1:
        return SExp(args[0].type - 1)
    raise ReduceError("type takes exactly one parameter")


def op_var(args):
    if len(args) == 1 and args[0].type == ATOM_TYPES.VAR:
        return SExp(args[0].var_index())
    raise ReduceError("type takes exactly one parameter, which must be a var")


def op_is_null(args):
    if len(args) == 1:
        return SExp(args[0].is_list() and len(args[0]) == 0)
    raise ReduceError("is_null takes exactly one parameter, got %d" % len(args))


def op_get_raw(args):
    if len(args) != 2:
        raise ReduceError("get_raw takes exactly 2 parameters, got %d" % len(args))
    item, index = args[0], args[1]
    if not item.is_list():
        raise ReduceError("get_raw got non-list: %s" % item)
    if not index.is_bytes():
        raise ReduceError("get_raw bad index type: %s" % index)
    if 0 <= index.as_int() < len(item):
        return SExp(item[index.as_int()])
    raise ReduceError("get_raw bad index %d" % index.as_int())


# fail


def op_raise(args):
    raise ReduceError(args)


# logical operators


def op_equal(args):
    if len(args) != 2:
        raise ReduceError("equal requires 2 arguments, got %d" % len(args))
    a0, a1 = args
    if a0.type != a1.type:
        return S_False
    if a0.type == ATOM_TYPES.PAIR:
        return S_False
    if a0.type == ATOM_TYPES.VAR:
        return SExp(a0.var_index() == a1.var_index())
    return SExp(a0.as_bytes() == a1.as_bytes())
