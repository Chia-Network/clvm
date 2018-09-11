import binascii

from .compile import compile_text
from .reduce import reduce
from .serialize import unwrap_blob


def check_solution(script_hash, solution_blob):
    script_hash_hex = binascii.hexlify(script_hash).decode()
    canonical_script_text = "((reduce x0 x1) (equal (sha256 x0) 0x%s))" % script_hash_hex
    script_bin = compile_text(canonical_script_text)
    bind_values = unwrap_blob(solution_blob)
    reductions = reduce(unwrap_blob(script_bin), bind_values)
    return reductions
