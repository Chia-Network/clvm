# read strings into Token

from opacity.RExp import subclass_rexp


class TokenMixin:
    @classmethod
    def to(class_, v, offset=None):
        s = super(TokenMixin, class_).to(v)
        if not hasattr(s, "_offset") or s._offset is None:
            s._offset = offset
        return s

    def __iter__(self):
        return self.as_iter()


tokenize = subclass_rexp(TokenMixin, (str, bytes))


def consume_whitespace(s: str, offset):
    """
    This also deals with comments.
    """
    while True:
        while offset < len(s) and s[offset].isspace():
            offset += 1
        if offset >= len(s) or s[offset] != ";":
            break
        while offset < len(s) and s[offset] not in "\n\r":
            offset += 1
    return offset


def consume_until_whitespace(s: str, offset):
    start = offset
    while offset < len(s) and not s[offset].isspace() and s[offset] != ")":
        offset += 1
    return s[start:offset], offset


def tokenize_str(s: str, offset):
    start = offset
    initial_c = s[start]
    offset += 1
    while offset < len(s) and s[offset] != initial_c:
        offset += 1
    if offset < len(s):
        token = tokenize(s[start:offset+1], start)
        return token, offset + 1
    raise SyntaxError("unterminated string starting at %d: %s" % (start, s[start:]))


def tokenize_list(s: str, offset):
    c = s[offset]
    assert c == "("
    initial_offset = offset
    offset += 1

    offset = consume_whitespace(s, offset)

    r = []
    while offset < len(s):
        c = s[offset]

        if c == ")":
            return tokenize(r, initial_offset), offset + 1

        t, offset = tokenize_sexp(s, offset)
        r.append(t)
        offset = consume_whitespace(s, offset)

    raise SyntaxError("missing )")


def tokenize_atom(s: str, offset):
    c = s[offset]
    if c in "\'\"":
        return tokenize_str(s, offset)

    start_offset = offset
    item, offset = consume_until_whitespace(s, offset)
    return tokenize(item, start_offset), offset


def tokenize_sexp(s: str, offset: int):
    offset = consume_whitespace(s, offset)

    if s[offset] == ")":
        raise SyntaxError("unexpected ) at %d" % offset)

    if s[offset] == "(":
        return tokenize_list(s, offset)

    return tokenize_atom(s, offset)


def read_tokens(s: str):
    return tokenize_sexp(s, 0)[0]
