import hashlib

from opacity.compile import compile_to_blob, compile_to_sexp, disassemble, parse_macros, tokenize_program

from opacity.SExp import SExp
from opacity.reduce import reduce


def test_top_level_script():
    script_source = "((equal (sha256 x1) x0) (reduce (unwrap x1) (unwrap x2)))"
    script_bin = compile_to_blob(script_source)
    underlying_script = compile_to_blob("((equal x0 500) (equal x1 600) (equal x2 (+ x0 x1)))")
    p2sh = hashlib.sha256(underlying_script).digest()
    bindings = [p2sh, underlying_script, SExp([500, 600, 1100]).as_bin()]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 1

    bindings = [p2sh, underlying_script, SExp([500, 600, 1101]).as_bin()]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 0


def test_tokenize_comments():
    script_source = "(equal 7 (+ 5 ;foo bar\n   2))"
    t = tokenize_program(script_source)
    assert t == ["equal", "7", ["+", "5", "2"]]


def test_compile_macro():
    macro_source = "((macro (foo a b c) (equal a (+ b c))))"
    macros = parse_macros(macro_source)
    script_source = "((foo 15 5 10) (foo 50 40 30))"
    script_bin = compile_to_blob(script_source, macros)
    v = disassemble(script_bin)
    assert v == "((equal 15 (+ 5 10)) (equal 50 (+ 40 30)))"
