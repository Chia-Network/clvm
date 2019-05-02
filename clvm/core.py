from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens

from .ReduceError import ReduceError


def make_reduce_f(operator_lookup, quote_kw, reduce_kw, env_kw):

    def reduce_core(reduce_f, form, env):
        if not form.listp():
            raise ReduceError("%s is not a list" % form)

        if form.nullp():
            raise ReduceError("reduce_list cannot handle empty list")

        first_item = form.first()

        f_index = first_item.as_atom()
        if f_index is None:
            raise ReduceError("non-byte atom %s in first element of list" % first_item)

        # special form QUOTE

        if f_index == quote_kw:
            if form.rest().nullp() or not form.rest().rest().nullp():
                raise ReduceError("quote requires exactly 1 parameter, got %d" % (
                    len(list(form.as_iter())) - 1))
            return form.rest().first()

        # TODO: rewrite with cons, rest, etc.
        args = form.to([reduce_f(reduce_f, _, env) for _ in form.rest().as_iter()])

        # keyword REDUCE

        if f_index == reduce_kw:
            if args.rest().nullp() or not args.rest().rest().nullp():
                raise ReduceError("reduce_list requires 2 parameters, got %d" % len(list(args.as_iter())))
            return reduce_f(reduce_f, args.first(), args.rest().first())

        # keyword ENV

        if f_index == env_kw:
            if form.nullp() or not form.rest().nullp():
                raise ReduceError("env requires no parameters, got %d" % (list(args.as_iter())))
            return env

        # special form APPLY

        f = operator_lookup.get(f_index)
        if f:
            return f(args)

        raise ReduceError("unknown function index %s" % f_index)

    return reduce_core


def operators_for_dict(keyword_to_atom, op_dict, op_name_lookup={}):
    d = {}
    for op in keyword_to_atom.keys():
        op_name = "op_%s" % op_name_lookup.get(op, op)
        op_f = op_dict.get(op_name)
        if op_f:
            d[keyword_to_atom[op]] = op_f
    return d


def operators_for_module(keyword_to_atom, mod, op_name_lookup={}):
    return operators_for_dict(keyword_to_atom, mod.__dict__, op_name_lookup)


def build_runtime(
    to_sexp_f, keyword_from_atom, keyword_to_atom,
        operator_lookup, qre_names=["quote", "reduce", "env"]):

    reduce_f = make_reduce_f(
        operator_lookup, keyword_to_atom[qre_names[0]],
        keyword_to_atom[qre_names[1]], keyword_to_atom[qre_names[2]])

    def transform(sexp):
        if sexp.listp():
            if sexp.nullp():
                return sexp
            sexp, args = sexp.first(), sexp.rest()
        else:
            args = sexp.null

        return reduce_f(reduce_f, sexp, args)

    def to_tokens(sexp):
        return to_int_keyword_tokens(sexp, keyword_from_atom)

    def from_tokens(sexp):
        ikt = from_int_keyword_tokens(sexp, keyword_to_atom)
        return to_sexp_f(ikt)

    return reduce_f, transform, to_tokens, from_tokens
