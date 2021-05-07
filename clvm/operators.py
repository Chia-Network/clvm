from typing import Dict, Tuple

from . import core_ops, more_ops

from .CLVMObject import CLVMObject
from .casts import int_to_bytes
from .op_utils import operators_for_module
from .handle_unknown_op import handle_unknown_op_softfork_ready as default_unknown_op

from .costs import (
    ARITH_BASE_COST,
    ARITH_COST_PER_BYTE,
    ARITH_COST_PER_ARG,
    MUL_BASE_COST,
    MUL_COST_PER_OP,
    MUL_LINEAR_COST_PER_BYTE,
    MUL_SQUARE_COST_PER_BYTE_DIVIDER,
    CONCAT_BASE_COST,
    CONCAT_COST_PER_ARG,
    CONCAT_COST_PER_BYTE,
)

KEYWORDS = (
    # core opcodes 0x01-x08
    ". q a i c f r l x "

    # opcodes on atoms as strings 0x09-0x0f
    "= >s sha256 substr strlen concat . "

    # opcodes on atoms as ints 0x10-0x17
    "+ - * / divmod > ash lsh "

    # opcodes on atoms as vectors of bools 0x18-0x1c
    "logand logior logxor lognot . "

    # opcodes for bls 1381 0x1d-0x1f
    "point_add pubkey_for_exp . "

    # bool opcodes 0x20-0x23
    "not any all . "

    # misc 0x24
    "softfork "
).split()

KEYWORD_FROM_ATOM = {int_to_bytes(k): v for k, v in enumerate(KEYWORDS)}
KEYWORD_TO_ATOM = {v: k for k, v in KEYWORD_FROM_ATOM.items()}

OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "div",
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


def default_native_opcodes():
    if NativeOpLookup is None:
        return None

    d = {}
    for idx, name in KEYWORD_FROM_ATOM.items():
        # name = OP_REWRITE.get(name, name)
        if name in ".qa":
            continue
        d[name] = idx
    return d


## DEPRECATED below here


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
            self.unknown_op_handler = default_unknown_op
        return self

    def __call__(self, op: bytes, arguments: CLVMObject) -> Tuple[int, CLVMObject]:
        f = self.get(op)
        if f is None:
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
