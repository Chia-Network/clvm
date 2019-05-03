from clvm.runtime_001 import reduce_f
from opacity.binutils import assemble_from_symbols, disassemble_to_symbols, disassemble

def transform(sexp):
    if sexp.listp():
        if sexp.nullp():
            return sexp
        sexp, args = sexp.first(), sexp.rest()
    else:
        args = sexp.null

    return reduce_f(reduce_f, sexp, args)


def to_tokens(sexp):
    return disassemble_to_symbols(sexp)


def from_tokens(sexp):
    return assemble_from_symbols(sexp)
