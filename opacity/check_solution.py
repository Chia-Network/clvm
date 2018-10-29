import binascii

from .compile import compile_to_sexp
from .reduce import reduce
from .SExp import SExp


def check_solution(script_hash, solution_sexp):
    script_hash_hex = binascii.hexlify(script_hash).decode()
    canonical_script_text = "((reduce x0 x1) (equal (sha256 x0) 0x%s))" % script_hash_hex
    script_sexp = compile_to_sexp(canonical_script_text)
    reductions = reduce(script_sexp, solution_sexp)
    return reductions
