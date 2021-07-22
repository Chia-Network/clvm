from .casts import int_to_bytes

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

KEYWORD_TO_LONG_KEYWORD = {
    "i": "op_if",
    "c": "op_cons",
    "f": "op_first",
    "r": "op_rest",
    "l": "op_listp",
    "x": "op_raise",
    "=": "op_eq",
    "+": "op_add",
    "-": "op_subtract",
    "*": "op_multiply",
    "/": "op_divmod",
    ">": "op_gr",
    ">s": "op_gr_bytes",
}
