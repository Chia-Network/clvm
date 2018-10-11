import binascii

from .compile import compile_text
from .reduce import reduce
from .SExp import SExp


def check_solution(script_hash, solution_sexp):
    script_hash_hex = binascii.hexlify(script_hash).decode()
    canonical_script_text = "((reduce x0 x1) (equal (sha256 x0) 0x%s))" % script_hash_hex
    script_bin = compile_text(canonical_script_text)
    reductions = reduce(SExp.from_blob(script_bin), solution_sexp)
    return reductions
