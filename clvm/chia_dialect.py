from . import core_ops, more_ops

from .casts import int_to_bytes
from .dialect import DialectInfo
from .op_utils import operators_for_module


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


def chia_dialect_info():
    op_lookup = operators_for_module(KEYWORD_TO_ATOM, core_ops, OP_REWRITE)
    op_lookup.update(operators_for_module(KEYWORD_TO_ATOM, more_ops, OP_REWRITE))
    return DialectInfo(KEYWORD_TO_ATOM["q"], KEYWORD_TO_ATOM["a"], op_lookup)
