from opacity import core_operators

from opacity.core import make_reduce_f
from opacity.SExp import to_sexp_f

from . import more_operators
from .corevm_0_0_1 import build_runtime, operators_for_module


CORE_KEYWORDS = ". quote reduce cons first rest type var env is_null get raise equal".split()

MORE_KEYWORDS = (
    "sha256 + - * . wrap unwrap point_add pubkey_for_exp").split()

KEYWORD_FROM_INT = CORE_KEYWORDS + MORE_KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}


OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
}


KEYWORD_FROM_INT = CORE_KEYWORDS + MORE_KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}

OPERATOR_LOOKUP = operators_for_module(KEYWORD_TO_INT, core_operators)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_INT, more_operators, OP_REWRITE))

reduce_f, transform, to_tokens, from_tokens = build_runtime(to_sexp_f, KEYWORD_FROM_INT, KEYWORD_TO_INT, OPERATOR_LOOKUP)
