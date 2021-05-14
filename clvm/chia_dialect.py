try:
    from clvm_rs import (
        native_opcodes_dict,
        Dialect as NativeDialect,
        NATIVE_OP_UNKNOWN_NON_STRICT,
        NATIVE_OP_UNKNOWN_STRICT,
    )
except ImportError:
    NativeDialect = native_opcodes_dict = None

from . import core_ops, more_ops

from .casts import int_to_bytes
from .dialect import ConversionFn, Dialect
from .handle_unknown_op import (
    handle_unknown_op_softfork_ready,
    handle_unknown_op_strict,
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


def op_table_for_module(mod):
    return {k: v for k, v in mod.__dict__.items() if k.startswith("op_")}


def chia_operator_table():
    if native_opcodes_dict:
        return native_opcodes_dict()
    table = {}
    table.update(op_table_for_module(core_ops))
    table.update(op_table_for_module(more_ops))
    return table


def chia_dialect_op_lookup(keyword_to_atom, op_rewrite):
    op_table = chia_operator_table()
    op_lookup = {}
    for op, bytecode in keyword_to_atom.items():
        if op in "qa.":
            continue
        op_name = "op_%s" % op_rewrite.get(op, op)
        op_f = op_table[op_name]
        op_lookup[bytecode] = op_f
    return op_lookup


def chia_dialect(strict: bool, to_python: ConversionFn) -> Dialect:
    quote_kw = KEYWORD_TO_ATOM["q"]
    apply_kw = KEYWORD_TO_ATOM["a"]
    opcode_lookup = chia_dialect_op_lookup(KEYWORD_TO_ATOM, OP_REWRITE)
    if NativeDialect:
        unknown_op_callback = (
            NATIVE_OP_UNKNOWN_STRICT if strict else NATIVE_OP_UNKNOWN_NON_STRICT
        )
        dialect = NativeDialect(
            quote_kw,
            apply_kw,
            unknown_op_callback,
            to_python=to_python,
        )
    else:
        unknown_op_callback = (
            handle_unknown_op_strict if strict else handle_unknown_op_softfork_ready
        )
        dialect = Dialect(
            quote_kw,
            apply_kw,
            unknown_op_callback,
            to_python=to_python,
        )
    dialect.update(opcode_lookup)
    return dialect
