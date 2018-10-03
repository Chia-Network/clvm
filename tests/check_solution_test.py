import binascii
import hashlib

from opacity.check_solution import check_solution
from opacity.compile import compile_text
from opacity.serialize import to_sexp


def test_check_solution_1():
    EXPECTED_HASH = b'8c7ed90bb159148a49e276acc95298ef3201adfffed38af9a4972cef34225e45'
    encumber_script = "(equal x0 100)"
    compiled_script = compile_text(encumber_script)
    script_hash = hashlib.sha256(compiled_script).digest()
    assert binascii.hexlify(script_hash) == EXPECTED_HASH
    underlying_solution = compile_text("(100)")
    solution_blob = to_sexp([compiled_script, underlying_solution])
    r = check_solution(script_hash, solution_blob)
    assert r == 1


def test_check_solution_2():
    EXPECTED_HASH = b'90e809495aebabb5a2244e90c51f324964fde78245bf3432c564c0b6f8d1564b'
    encumber_script = "((equal x0 (+ x1 x2)) (equal x1 17) (equal x0 30))"
    compiled_script = compile_text(encumber_script)
    script_hash = hashlib.sha256(compiled_script).digest()
    assert binascii.hexlify(script_hash) == EXPECTED_HASH
    underlying_solution = compile_text("(30 17 13)")
    solution_blob = to_sexp([compiled_script, underlying_solution])
    r = check_solution(script_hash, solution_blob)
    assert r == 1
