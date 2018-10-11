import binascii
import hashlib

from opacity.check_solution import check_solution
from opacity.compile import compile_text
from opacity.SExp import SExp


def do_test(expected_hash, encumber_script, solution_script):
    compiled_script = compile_text(encumber_script)
    script_hash = hashlib.sha256(compiled_script).digest()
    assert binascii.hexlify(script_hash) == expected_hash.encode("utf8")
    underlying_solution = compile_text(solution_script)
    solution_blob = SExp([compiled_script, underlying_solution])
    r = check_solution(script_hash, solution_blob)
    assert r == 1


def test_check_solution_1():
    encumber_script = "(equal x0 100)"
    expected_hash = '8d0cb0dc670c3b45789afcaf5e2b59915e7b8c236fe52f6200c4ec1e37a7d504'
    do_test(expected_hash, encumber_script, "(100)")


def test_check_solution_2():
    encumber_script = "((equal x0 (+ x1 x2)) (equal x1 17) (equal x0 30))"
    expected_hash = 'b0d5588a9a246d384e8d748aa25e66a976874f7b943a82958ee8e9c7e8e09ae7'
    do_test(expected_hash, encumber_script, "(30 17 13)")
