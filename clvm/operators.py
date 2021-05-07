# this API is deprecated in favor of dialects. See `dialect.py` and `chia_dialect.py`

from typing import Dict, Tuple

from . import core_ops, more_ops

from .CLVMObject import CLVMObject
from .op_utils import operators_for_module
from .handle_unknown_op import handle_unknown_op_softfork_ready
from .chia_dialect import KEYWORDS, OP_REWRITE, KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM  # noqa


class OperatorDict(dict):
    """
    This is a nice hack that adds `__call__` to a dictionary, so
    operators can be added dynamically.
    """

    def __new__(class_, d: Dict, *args, **kwargs):
        """
        `quote_atom` and `apply_atom` must be set
        `unknown_op_handler` has a default implementation
        We do not check if quote and apply are distinct
        We do not check if the opcode values for quote and apply exist in the passed-in dict
        """
        self = super(OperatorDict, class_).__new__(class_, d)
        self.quote_atom = kwargs["quote"] if "quote" in kwargs else d.quote_atom
        self.apply_atom = kwargs["apply"] if "apply" in kwargs else d.apply_atom
        if "unknown_op_handler" in kwargs:
            self.unknown_op_handler = kwargs["unknown_op_handler"]
        else:
            self.unknown_op_handler = handle_unknown_op_softfork_ready
        return self

    def __call__(self, op: bytes, arguments: CLVMObject) -> Tuple[int, CLVMObject]:
        f = self.get(op)
        if f is None:
            try:
                return self.unknown_op_handler(op, arguments, max_cost=None)
            except TypeError:
                return self.unknown_op_handler(op, arguments)
        else:
            return f(arguments)


QUOTE_ATOM = KEYWORD_TO_ATOM["q"]
APPLY_ATOM = KEYWORD_TO_ATOM["a"]

OPERATOR_LOOKUP = OperatorDict(
    operators_for_module(KEYWORD_TO_ATOM, core_ops, OP_REWRITE),
    quote=QUOTE_ATOM,
    apply=APPLY_ATOM,
)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_ATOM, more_ops, OP_REWRITE))
