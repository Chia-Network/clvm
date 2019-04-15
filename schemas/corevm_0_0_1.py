from opacity import core_operators

from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens
from opacity.core import make_reduce_f
from opacity.SExp import SExp

CORE_KEYWORDS = ". quote reduce cons first rest type var env is_null get raise equal".split()

KEYWORD_FROM_INT = CORE_KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}


OPERATOR_LOOKUP = {KEYWORD_TO_INT[op]: getattr(
    core_operators, "op_%s" % op, None) for op in KEYWORD_TO_INT.keys()}

REDUCE_F = make_reduce_f(OPERATOR_LOOKUP, KEYWORD_TO_INT)


def transform(sexp):
    if sexp.is_list():
        if len(sexp) == 0:
            return sexp
        sexp, args = sexp[0], sexp[1:]
    else:
        args = SExp([])

    return REDUCE_F(REDUCE_F, sexp, args)


def to_tokens(sexp):
    return to_int_keyword_tokens(sexp, KEYWORD_FROM_INT)


def from_tokens(sexp):
    return from_int_keyword_tokens(sexp, KEYWORD_TO_INT)
