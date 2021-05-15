from .casts import int_to_bytes
from .dialect import ConversionFn, Dialect, new_dialect, opcode_table_for_backend

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


def chia_dialect(strict: bool, to_python: ConversionFn, backend=None) -> Dialect:
    quote_kw = KEYWORD_TO_ATOM["q"]
    apply_kw = KEYWORD_TO_ATOM["a"]
    dialect = new_dialect(quote_kw, apply_kw, strict, to_python, backend=backend)
    table = opcode_table_for_backend(KEYWORD_TO_ATOM, backend=backend)
    dialect.update(table)
    return dialect
