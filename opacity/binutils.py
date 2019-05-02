from clvm.runtime_001 import KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, to_sexp_f

from .int_keyword import from_int_keyword_tokens, to_int_keyword_tokens
from .reader import read_tokens
from .writer import write_tokens


def assemble_from_symbols(sexp):
    ikt = from_int_keyword_tokens(sexp, KEYWORD_TO_ATOM)
    return to_sexp_f(ikt)


def disassemble_to_symbols(sexp):
    return to_int_keyword_tokens(sexp, KEYWORD_FROM_ATOM)


def disassemble(sexp):
    symbols = disassemble_to_symbols(sexp)
    return write_tokens(symbols)


def assemble(s):
    symbols = read_tokens(s)
    return assemble_from_symbols(symbols)
