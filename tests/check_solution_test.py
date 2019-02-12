import binascii
import hashlib

from opacity.check_solution import check_solution
from opacity.compile import compile_to_blob
from opacity.SExp import SExp


def do_test(expected_hash, encumber_script, solution, response):
    compiled_script = compile_to_blob(encumber_script)
    script_hash = hashlib.sha256(compiled_script).digest()
    assert binascii.hexlify(script_hash) == expected_hash.encode("utf8")
    underlying_solution = SExp(solution)
    solution_sexp = SExp([SExp.from_blob(compiled_script), underlying_solution])
    r = check_solution(script_hash, solution_sexp)
    assert r == response


def test_check_solution_1():
    encumber_script = "(equal x0 100)"
    expected_hash = '8d0cb0dc670c3b45789afcaf5e2b59915e7b8c236fe52f6200c4ec1e37a7d504'
    solution = [100]
    do_test(expected_hash, encumber_script, solution, 1)


def test_check_solution_2():
    encumber_script = "(and (equal x0 (+ x1 x2)) (equal x1 17) (equal x0 30))"
    expected_hash = '9dde76feb02311c1c9d5f07337e8c99a555b2e0e12ab470d00fd691030dc4fd3'
    solution = [30, 17, 13]
    do_test(expected_hash, encumber_script, solution, 1)


def test_assert_output():
    encumber_script = "(reduce (unwrap x0) (unwrap x1))"
    expected_hash = 'c220d98abd647802c5fa36867182cff04a679d0e2d9a839fb7855e24cde2c28b'
    x0 = compile_to_blob("(assert_output 500 600 700)")
    x1 = SExp([]).as_bin()
    solution = [x0, x1]
    expected = SExp.from_blob(compile_to_blob("(and (assert_output 500 600 700) 1)"))
    do_test(expected_hash, encumber_script, solution, expected)

    x0 = compile_to_blob("(and (equal 55 (+ x0 9)) (assert_output 500 600 700) (equal 10025 x1 (+ x2 25)))")
    x1 = SExp([46, 10025, 10000]).as_bin()
    solution = [x0, x1]
    expected = SExp.from_blob(compile_to_blob("(and (and 1 (assert_output 500 600 700) 1) 1)"))
    do_test(expected_hash, encumber_script, solution, expected)
