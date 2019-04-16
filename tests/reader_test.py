from opacity.reader import read_tokens
from opacity.writer import write_tokens


def test_tokenize_comments():
    script_source = "(equal 7 (+ 5 ;foo bar\n   2))"
    expected_output = "(equal 7 (+ 5 2))"
    t = read_tokens(script_source)
    s = write_tokens(t)
    assert s == expected_output
