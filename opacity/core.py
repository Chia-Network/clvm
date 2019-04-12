from . import core_operators

from .ReduceError import ReduceError
from .SExp import SExp


def make_reduce_f(operator_lookup, keyword_to_int):

    keyword_from_int = {v: k for k, v in keyword_to_int.items()}

    QUOTE_KEYWORD = keyword_to_int["quote"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]
    ENV_KEYWORD = keyword_to_int["env"]

    def reduce_core(reduce_f, form, env):
        if not form.is_list():
            raise ReduceError("%s is not a list" % form)

        if len(form) == 0:
            raise ReduceError("reduce_list cannot handle empty list")

        first_item = form[0]

        if not first_item.is_bytes():
            raise ReduceError("non-byte atom %s in first element of list" % first_item)

        f_index = first_item.as_int()

        # special form QUOTE

        if f_index == QUOTE_KEYWORD:
            if len(form) != 2:
                raise ReduceError("quote requires exactly 1 parameter, got %d" % (len(form) - 1))
            return form[1]

        # TODO: rewrite with cons, rest, etc.
        args = SExp([reduce_f(reduce_f, _, env) for _ in form[1:]])

        # keyword REDUCE

        if f_index == REDUCE_KEYWORD:
            if len(args) != 2:
                raise ReduceError("reduce_list requires 2 parameters, got %d" % len(args))
            return reduce_f(reduce_f, args[0], args[1])

        # keyword ENV

        if f_index == ENV_KEYWORD:
            if len(form) != 1:
                raise ReduceError("env requires no parameters, got %d" % (len(form) - 1))
            return env

        # special form APPLY

        f = operator_lookup.get(f_index)
        if f:
            return f(args)

        msg = "unknown function index %d" % f_index
        if f_index in keyword_from_int:
            msg += ' for keyword "%s"' % keyword_from_int[f_index]
        raise ReduceError(msg)

    return reduce_core
