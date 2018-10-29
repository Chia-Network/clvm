import binascii
import hashlib

from opacity.compile import compile_to_blob, compile_to_sexp, disassemble, parse_macros, tokenize_program

from opacity.SExp import SExp, Var
from opacity.reduce import reduce


def test_1():
    pubkey_text = hashlib.sha256(b'').hexdigest()
    input = "(((equal (sha256 x0) 0x%s)) (reduce x0 x2))" % pubkey_text
    result = compile_to_blob(input)
    d = binascii.unhexlify("2221230822094080%s230a4042" % pubkey_text)
    assert result == d
    t = disassemble(result)
    assert t == input


def test_compile_disassemble():
    SCRIPTS = [
        "(((equal (sha256 x0) x1)) (reduce x1 x2))",
        #"(sha256 'hello' 'there')",
        #"(sha256 'the quick brown fox jumps ' 'over the lazy dogs')",
        #'(sha256 "the quick brown fox jumps" " over the lazy dogs")',
    ]
    for _ in SCRIPTS:
        script_bin = compile_to_sexp(_)
        script_disassembled = disassemble(script_bin)
        assert script_disassembled == _


def test_p2sh():
    underlying_script = compile_to_blob("((equal x0 500) (equal x1 600))")
    script_source = "((equal (sha256 x0) 0x%s) (reduce x0 x1))" % hashlib.sha256(
        underlying_script).hexdigest()
    bindings = [underlying_script, SExp([500, 600]).as_bin()]
    v = reduce(compile_to_sexp(script_source), bindings)
    assert v == 1

    bindings[-1] = SExp([500, 599]).as_bin()
    v = reduce(compile_to_sexp(script_source), bindings)
    assert v == 0


def test_top_level_script():
    script_source = "((equal (sha256 x1) x0) (reduce x1 x2))"
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
