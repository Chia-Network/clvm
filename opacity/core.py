from .ReduceError import ReduceError

# TODO remove this
from .casts import int_from_bytes


def make_reduce_f(operator_lookup, keyword_to_int):

    keyword_from_int = {v: k for k, v in keyword_to_int.items()}

    QUOTE_KEYWORD = keyword_to_int["quote"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]
    ENV_KEYWORD = keyword_to_int["env"]

    def reduce_core(reduce_f, form, env):
        if not form.listp():
            raise ReduceError("%s is not a list" % form)

        if form.nullp():
            raise ReduceError("reduce_list cannot handle empty list")

        first_item = form.first()

        if not first_item.is_bytes():
            raise ReduceError("non-byte atom %s in first element of list" % first_item)

        f_index = int_from_bytes(first_item.as_atom())

        # special form QUOTE

        if f_index == QUOTE_KEYWORD:
            if form.rest().nullp() or not form.rest().rest().nullp():
                raise ReduceError("quote requires exactly 1 parameter, got %d" % (len(form) - 1))
            return form[1]

        # TODO: rewrite with cons, rest, etc.
        args = form.__class__([reduce_f(reduce_f, _, env) for _ in form[1:]])

        # keyword REDUCE

        if f_index == REDUCE_KEYWORD:
            if args.rest().nullp() or not args.rest().rest().nullp():
                raise ReduceError("reduce_list requires 2 parameters, got %d" % len(args))
            return reduce_f(reduce_f, args[0], args[1])

        # keyword ENV

        if f_index == ENV_KEYWORD:
            if form.nullp() or not form.rest().nullp():
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
