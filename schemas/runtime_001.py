from clvm.runtime_001 import eval_f, to_sexp_f
from clvm.serialize import sexp_from_stream
from opacity.binutils import assemble_from_symbols, disassemble, disassemble_to_symbols


def transform(sexp):
    if sexp.listp():
        if sexp.nullp():
            return sexp
        sexp, args = sexp.first(), sexp.rest()
    else:
        args = sexp.null

    return eval_f(eval_f, sexp, args)


def to_tokens(sexp):
    return disassemble_to_symbols(sexp)


def from_tokens(sexp):
    return assemble_from_symbols(sexp)


def from_stream(f):
    return sexp_from_stream(f, to_sexp_f)
