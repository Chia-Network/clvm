from opacity import core_operators

from opacity.compile import compile_token
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



def dump(form, keywords=[], is_first_element=False):
    if form.is_list():
        return SExp([dump(f, keywords, _ == 0) for _, f in enumerate(form)])

    if form.is_var():
        return SExp(("x%d" % form.var_index()).encode("utf8"))

    if is_first_element and 0 <= form.as_int() < len(keywords):
        v = keywords[form.as_int()]
        if v != '.':
            return v.encode("utf8")

    if len(form.as_bytes()) > 4:
        return SExp("0x%s" % binascii.hexlify(form.as_bytes()).encode("utf8"))

    return SExp(("%d" % form.as_int()).encode("utf8"))


def to_tokens(sexp):
    return dump(sexp, KEYWORD_FROM_INT)


def from_tokens(sexp):
    return compile_token(sexp, KEYWORD_TO_INT)
