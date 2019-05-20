import binascii

from clvm.subclass_sexp import subclass_sexp, EvalError

from .Node import Node


class mixin:
    @classmethod
    def to_castable(class_, v):
        if isinstance(v, Node):
            return v.path()
        return v

    @classmethod
    def to_atom(class_, v):
        if isinstance(v, bytes):
            v = "0x%s" % binascii.hexlify(v).decode("utf8")
        if isinstance(v, int):
            return str(v)
        return v

    def as_int(self):
        return int(self.v)

    def as_bytes(self):
        if not self.listp():
            as_atom = self.as_atom()
            if len(as_atom) > 1:
                try:
                    if as_atom[0] == as_atom[-1] == '"':
                        return as_atom[1:-1].encode("utf8")
                    if as_atom.upper().startswith("0X"):
                        return binascii.unhexlify(as_atom[2:])
                except Exception:
                    pass
        raise EvalError("not bytes", self)

    def __repr__(self):
        if self.nullp():
            return "()"
        if isinstance(self.v, str):
            return self.v
        return "(%s)" % (" ".join(repr(_) for _ in self.as_iter()))


to_sexp = subclass_sexp(mixin, (str, None.__class__), true="true", false=None)


def Token(s, offset):
    t = to_sexp(s)
    t._offset = offset
    return t


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
        token = Token(s[start:offset+1], start)
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
            return Token(r, initial_offset), offset + 1

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
    return Token(item, start_offset), offset


def tokenize_sexp(s: str, offset: int):
    offset = consume_whitespace(s, offset)

    if s[offset] == ")":
        raise SyntaxError("unexpected ) at %d" % offset)

    if s[offset] == "(":
        return tokenize_list(s, offset)

    return tokenize_atom(s, offset)


def read_tokens(s: str):
    return tokenize_sexp(s, 0)[0]
