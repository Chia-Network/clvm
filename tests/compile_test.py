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


def test_simple_add():
    script_source = "(+ 10 20)"
    script_sexp = compile_to_sexp(script_source)
    t = disassemble(script_sexp)
    assert t == script_source
    v = reduce(script_sexp, [])
    assert v == 30


def test_var_binding():
    script_source = "x0"
    script_sexp = compile_to_sexp(script_source)
    t = disassemble(script_sexp)
    assert t == script_source
    blob = b"foobarbaz"
    v = reduce(script_sexp, [blob])
    assert v == blob

    script_source = "x3"
    script_sexp = compile_to_sexp(script_source)
    t = disassemble(script_sexp)
    assert t == script_source
    junk = b"junk"
    blob = b"foobarbaz"
    v = reduce(script_sexp, [junk, junk, junk, blob, junk])
    assert v == blob


def test_sha256():
    blob = b"hello.there.my.dear.friend"
    hashed_value = hashlib.sha256(blob).digest()
    script_source = "(sha256 x0)"
    script_sexp = compile_to_sexp(script_source)
    t = disassemble(script_sexp)
    assert t == script_source
    v = reduce(script_sexp, [blob])
    assert v == hashed_value

    s = blob.decode("utf8")
    script_source = "(sha256 '%s' '%s')" % (s[:3], s[3:])
    v = reduce(compile_to_sexp(script_source), [])
    assert v == hashed_value

    script_source = "(sha256 x0 x1)"
    v = reduce(compile_to_sexp(script_source), [blob[:3], blob[3:]])
    assert v == hashed_value


def test_nested():
    script_source = "(+ (+ 5 x0) x1)"
    v = reduce(compile_to_sexp(script_source), [9, 1000])
    assert v == 1014


def test_implicit_and():
    script_source = "((equal 1 1) (equal 2 2) (equal 3 3))"
    v = reduce(compile_to_sexp(script_source), [])
    assert v == 1

    script_source = "((equal 1 1) (equal 2 4) (equal 3 3))"
    v = reduce(compile_to_sexp(script_source), [])
    assert v == 0

    script_source = "((equal 1 2) (equal 2 2) (equal 3 3))"
    v = reduce(compile_to_sexp(script_source), [])
    assert v == 0


def test_equal():
    script_source = "(equal 2 3)"
    v = reduce(compile_to_sexp(script_source), [])
    assert v == 0

    script_source = "(equal 3 3)"
    v = reduce(compile_to_sexp(script_source), [])
    assert v == 1

    script_source = "(equal x0 (+ x1 x2))"
    v = reduce(compile_to_sexp(script_source), [7, 3, 4])
    assert v == 1

    script_source = "(equal x0 (+ x1 x2))"
    v = reduce(compile_to_sexp(script_source), [7, 3, 3])
    assert v == 0


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


def test_choose1():
    script_source = "(choose1 x0 (equal 500 x1) (equal 600 x1))"
    script_bin = compile_to_blob(script_source)

    bindings = [0, 500]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 1

    bindings = [0, 600]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 0

    bindings = [1, 600]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 1

    bindings = [1, 500]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 0

    bindings = [-20, 500]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 0

    bindings = [-20, 600]
    v = reduce(SExp.from_blob(script_bin), bindings)
    assert v == 0


def test_partial_bindings():
    script_source = "((equal 400 x0) (equal 500 x1) (equal 600 x2))"
    script_bin = compile_to_blob(script_source)

    bindings = [400]
    v = disassemble((reduce(SExp.from_blob(script_bin), bindings)).as_bin())
    assert v == "((equal 500 x1) (equal 600 x2))"

    bindings = [Var(7), 500]
    v = disassemble((reduce(SExp.from_blob(script_bin), bindings)).as_bin())
    assert v == "((equal 400 x7) (equal 600 x2))"


def test_tokenize_comments():
    script_source = "(equal 7 (+ 5 ;foo bar\n   2))"
    t = tokenize_program(script_source)
    assert t == ["equal", "7", ["+", "5", "2"]]


def test_compile_unterminated_str():
    script_source = "(equal 'foo 100)"
    try:
        compile_to_blob(script_source)
        assert 0
    except SyntaxError as ex:
        msg = ex.msg
        assert msg == "unterminated string starting at 7: 'foo 100)"


def test_compile_invalid_hex():
    for h in ["1009f", "1abefg"]:
        script_source = "(equal x0 0x%s)" % h
        try:
            compile_to_blob(script_source)
            assert 0
        except SyntaxError as ex:
            msg = ex.msg
            assert msg == "invalid hex at 10: 0x%s" % h


def test_compile_invalid_var():
    for v in ["xa", "x10038k", "x"]:
        script_source = "(equal x0 %s)" % v
        try:
            compile_to_blob(script_source)
            assert 0
        except SyntaxError as ex:
            msg = ex.msg
            assert msg == "invalid variable at 10: %s" % v


def test_compile_missing_close_paren():
    script_source = "(equal x0 100"
    try:
        compile_to_blob(script_source)
        assert 0
    except SyntaxError as ex:
        msg = ex.msg
        assert msg == "missing )"


def test_compile_unexpected_close_paren():
    script_source = ")"
    try:
        compile_to_blob(script_source)
        assert 0
    except SyntaxError as ex:
        msg = ex.msg
        assert msg == "unexpected ) at 0"


def test_compile_unparsable():
    script_source = "(foo bar)"
    try:
        compile_to_blob(script_source)
        assert 0
    except SyntaxError as ex:
        msg = ex.msg
        assert msg == "can't parse foo at 1"


def test_compile_macro():
    macro_source = "((macro (foo a b c) (equal a (+ b c))))"
    macros = parse_macros(macro_source)
    script_source = "((foo 15 5 10) (foo 50 40 30))"
    script_bin = compile_to_blob(script_source, macros)
    v = disassemble(script_bin)
    assert v == "((equal 15 (+ 5 10)) (equal 50 (+ 40 30)))"
