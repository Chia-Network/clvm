import io

from opacity.Var import Var

from . import core_ops, more_ops

from .casts import int_from_bytes, int_to_bytes
from .core import make_reduce_f
from .op_utils import operators_for_module
from .serialize import make_sexp_from_stream, sexp_to_stream
from .subclass_sexp import subclass_sexp


class mixin:
    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    @classmethod
    def from_blob(class_, blob):
        return sexp_from_stream(io.BytesIO(blob))

    def __iter__(self):
        return self.as_iter()


to_sexp_f = subclass_sexp(mixin, (bytes, Var))
sexp_from_stream = make_sexp_from_stream(to_sexp_f)

KEYWORDS = ". q e a i c f r l x = sha256 + - * . wrap unwrap point_add pubkey_for_exp".split()

OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
    "i": "if",
    "c": "cons",
    "f": "first",
    "r": "rest",
    "l": "listp",
    "x": "raise",
    "=": "eq",
}


KEYWORD_FROM_ATOM = {int_to_bytes(k): v for k, v in enumerate(KEYWORDS)}
KEYWORD_TO_ATOM = {v: k for k, v in KEYWORD_FROM_ATOM.items()}

OPERATOR_LOOKUP = operators_for_module(KEYWORD_TO_ATOM, core_ops, OP_REWRITE)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_ATOM, more_ops, OP_REWRITE))


reduce_f = make_reduce_f(
    OPERATOR_LOOKUP, KEYWORD_TO_ATOM["q"], KEYWORD_TO_ATOM["e"], KEYWORD_TO_ATOM["a"])
