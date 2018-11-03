from opacity.compile import compile_to_blob, disassemble, parse_macros, tokenize_program


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
