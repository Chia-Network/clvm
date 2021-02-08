from typing import Dict, Tuple

from . import core_ops, more_ops

from .CLVMObject import CLVMObject
from .EvalError import EvalError

from .casts import int_to_bytes
from .op_utils import operators_for_module

KEYWORDS = (
    ". q . a i c f r l x = sha256 + - * divmod "
    "substr strlen point_add pubkey_for_exp concat . > >s "
    "logand logior logxor lognot ash lsh "
    "not any all "
    "softfork div "
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

    def __new__(class_, d: Dict, *args, **kwargs):
        """
        `quote_atom` and `apply_atom` must be set
        `unknown_op_handler` has a default implementation
        """
        self = super(OperatorDict, class_).__new__(class_, d)
        self.quote_atom = kwargs["quote"] if "quote" in kwargs else d.quote_atom
        self.apply_atom = kwargs["apply"] if "apply" in kwargs else d.apply_atom
        if "unknown_op_handler" in kwargs:
            self.unknown_op_handler = kwargs["unknown_op_handler"]
        else:
            self.unknown_op_handler = self.unknown_op_raise
        return self

    def __call__(self, op: bytes, arguments: CLVMObject) -> Tuple[int, CLVMObject]:
        f = self.get(op)
        if f is None:
            def f(args):
                return self.unknown_op_handler(op, args)
        return f(arguments)

    def unknown_op_raise(self, op: bytes, arguments: CLVMObject):
        raise EvalError("unimplemented operator", arguments.to(op))


QUOTE_ATOM = KEYWORD_TO_ATOM["q"]
APPLY_ATOM = KEYWORD_TO_ATOM["a"]

OPERATOR_LOOKUP = OperatorDict(
    operators_for_module(KEYWORD_TO_ATOM, core_ops, OP_REWRITE), quote=QUOTE_ATOM, apply=APPLY_ATOM
)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_ATOM, more_ops, OP_REWRITE))
