from opacity import core_operators

from opacity.casts import int_from_bytes, int_to_bytes
from opacity.core import make_reduce_f
from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens

from opacity.SExp import to_sexp_f


CORE_KEYWORDS = ". quote reduce cons first rest type var env is_null get raise equal".split()


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


def build_runtime(to_sexp_f, keyword_from_atom, keyword_to_atom,
    operator_lookup, qre_names=["quote", "reduce", "env"]):

    reduce_f = make_reduce_f(operator_lookup, keyword_to_atom[qre_names[0]],
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
        return to_sexp_f(from_int_keyword_tokens(sexp, keyword_to_atom))

    return reduce_f, transform, to_tokens, from_tokens


# core vm

KEYWORD_FROM_ATOM = {int_to_bytes(k): v for k, v in enumerate(CORE_KEYWORDS)}
KEYWORD_TO_ATOM = {v: k for k, v in KEYWORD_FROM_ATOM.items()}

OPERATOR_LOOKUP = operators_for_module(KEYWORD_TO_ATOM, core_operators)

reduce_f, transform, to_tokens, from_tokens = build_runtime(to_sexp_f, KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, OPERATOR_LOOKUP)

