from typing import Callable, Dict, Tuple

from . import core_ops, more_ops

from .BaseSExp import BaseSExp
from .EvalError import EvalError

from .casts import int_to_bytes
from .op_utils import operators_for_module


KEYWORDS = (
    ". q . a i c f r l x = sha256 + - * divmod "
    "substr strlen point_add pubkey_for_exp concat sha256tree > >s "
    "logand logior logxor lognot ash lsh "
    "not any all "
    "softfork "
).split()

KEYWORD_FROM_ATOM = {int_to_bytes(k): v for k, v in enumerate(KEYWORDS)}
KEYWORD_TO_ATOM = {v: k for k, v in KEYWORD_FROM_ATOM.items()}

OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "i": "if",
    "c": "cons",
    "f": "first",
    "r": "rest",
    "l": "listp",
    "x": "raise",
    "=": "eq",
    ">": "gr",
    ">s": "gr_bytes",
}


class OperatorDict(dict):
    """
    This is a nice hack that adds `__call__` to a dictionary, so
    operators can be added dynamically.
    """

    def __new__(class_, d: Dict):
        self = super(OperatorDict, class_).__new__(class_, d)
        self.unknown_op_handler = self.unknown_op_raise
        return self

    def __call__(self, op: bytes, arguments: BaseSExp) -> Tuple[int, BaseSExp]:
        f = self.get(op)
        if f is None:
            f = lambda args: self.unknown_op_handler(op, args)
        return f(arguments)

    def set_unknown_op_handler(self, callback: Callable[[bytes, BaseSExp], Tuple[int, BaseSExp]]):
        self.unknown_op_handler = callback

    def unknown_op_raise(self, op: bytes, arguments: BaseSExp):
        raise EvalError("unimplemented operator", arguments.to(op))


OPERATOR_LOOKUP = OperatorDict(
    operators_for_module(KEYWORD_TO_ATOM, core_ops, OP_REWRITE)
)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_ATOM, more_ops, OP_REWRITE))
