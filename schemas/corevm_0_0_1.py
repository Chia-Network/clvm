from opacity import core_operators

from opacity.core import make_reduce_f
from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens

CORE_KEYWORDS = ". quote reduce cons first rest type var env is_null get raise equal".split()


def operators_for_dict(keyword_to_int, op_dict, op_name_lookup={}):
    d = {}
    for op in keyword_to_int.keys():
        op_name = "op_%s" % op_name_lookup.get(op, op)
        op_f = op_dict.get(op_name)
        if op_f:
            d[keyword_to_int[op]] = op_f
    return d


def operators_for_module(keyword_to_int, mod, op_name_lookup={}):
    return operators_for_dict(keyword_to_int, mod.__dict__, op_name_lookup)


def build_runtime(keyword_from_int, keyword_to_int, operator_lookup):

    reduce_f = make_reduce_f(operator_lookup, keyword_to_int)

    def transform(sexp):
        if sexp.is_list():
            if len(sexp) == 0:
                return sexp
            sexp, args = sexp[0], sexp[1:]
        else:
            args = sexp.__class__([])

        return reduce_f(reduce_f, sexp, args)


    def to_tokens(sexp):
        return to_int_keyword_tokens(sexp, keyword_from_int)


    def from_tokens(sexp):
        return from_int_keyword_tokens(sexp, keyword_to_int)

    return reduce_f, transform, to_tokens, from_tokens


# core vm

KEYWORD_FROM_INT = CORE_KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}

OPERATOR_LOOKUP = operators_for_module(KEYWORD_TO_INT, core_operators)

reduce_f, transform, to_tokens, from_tokens = build_runtime(KEYWORD_FROM_INT, KEYWORD_TO_INT, OPERATOR_LOOKUP)

