import binascii
import hashlib

from opacity.check_solution import check_solution
from opacity.compile import compile_text
from opacity.serialize import wrap_blobs


def test_check_solution_1():
    EXPECTED_HASH = b'd05ed703fffb2e267f620ea4f9658fe82d2ca09a6492146809ae405b2ce55341'
    encumber_script = "(equal x0 100)"
    compiled_script = compile_text(encumber_script)
    script_hash = hashlib.sha256(compiled_script).digest()
    assert binascii.hexlify(script_hash) == EXPECTED_HASH
    underlying_solution = compile_text("(100)")
    solution_blob = wrap_blobs([compiled_script, underlying_solution])
    r = check_solution(script_hash, solution_blob)
    assert r == 1


def test_check_solution_2():
    EXPECTED_HASH = b'1ddbc6912a183b11d1349c6f1945a9a78889ad103aa616528a643fbdc5e9b66b'
    encumber_script = "((equal x0 (+ x1 x2)) (equal x1 17) (equal x0 30))"
    compiled_script = compile_text(encumber_script)
    script_hash = hashlib.sha256(compiled_script).digest()
    assert binascii.hexlify(script_hash) == EXPECTED_HASH
    underlying_solution = compile_text("(30 17 13)")
    solution_blob = wrap_blobs([compiled_script, underlying_solution])
    r = check_solution(script_hash, solution_blob)
    assert r == 1
