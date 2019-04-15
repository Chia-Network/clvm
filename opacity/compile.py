# compiler

import binascii

from .SExp import SExp


class Token(str):
    def __new__(self, s, offset):
        self = str.__new__(self, s)
        self._offset = offset
        return self


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def parse_as_int(token):
    try:
        v = int(token)
        return SExp(v)
    except (ValueError, TypeError):
        pass


def parse_as_hex(token):
    if token[:2].upper() == "0X":
        try:
            return SExp(bytes_as_hex(binascii.unhexlify(token[2:])))
        except Exception:
            raise SyntaxError("invalid hex at %d: %s" % (token._offset, token))


def parse_as_var(token):
    if token[:1].upper() == "X":
        try:
            return SExp.from_var_index(int(token[1:]))
        except Exception:
            raise SyntaxError("invalid variable at %d: %s" % (token._offset, token))


def consume_whitespace(sexp: str, offset):
    """
    This also deals with comments.
    """
    while True:
        while offset < len(sexp) and sexp[offset].isspace():
            offset += 1
        if offset >= len(sexp) or sexp[offset] != ";":
            break
        while offset < len(sexp) and sexp[offset] not in "\n\r":
            offset += 1
    return offset


def consume_until_whitespace(sexp: str, offset):
    start = offset
    while offset < len(sexp) and not sexp[offset].isspace() and sexp[offset] != ")":
        offset += 1
    return sexp[start:offset], offset


def compile_atom(token, keyword_to_int):
    c = token[0]
    if c in "\'\"":
        assert c == token[-1] and len(token) >= 2
        return SExp(token[1:-1])

    if c == '#':
        keyword = token[1:].lower()
        keyword_id = keyword_to_int.get(keyword)
        if keyword_id is None:
            raise SyntaxError("unknown keyword: %s" % keyword)
        return SExp(keyword_id)

    for f in [parse_as_int, parse_as_var, parse_as_hex]:
        v = f(token)
        if v is not None:
            return v
    raise SyntaxError("can't parse %s at %d" % (token, token._offset))


def compile_list(tokens, keyword_to_int):
    if len(tokens) == 0:
        return SExp([])

    r = []
    if not tokens[0].is_list():
        keyword = keyword_to_int.get(tokens[0].as_bytes().decode("utf8").lower())
        if keyword:
            r.append(SExp(keyword))
            tokens = tokens[1:]

    for token in tokens:
        r.append(compile_token(token, keyword_to_int))

    return SExp(r)


def compile_token(token, keyword_to_int):
    if token.is_list():
        return compile_list(token, keyword_to_int)
    return compile_atom(token.as_bytes().decode("utf8"), keyword_to_int)


def tokenize_str(sexp: str, offset):
    start = offset
    initial_c = sexp[start]
    offset += 1
    while offset < len(sexp) and sexp[offset] != initial_c:
        offset += 1
    if offset < len(sexp):
        token = Token(sexp[start:offset+1], start)
        return token, offset + 1
    raise SyntaxError("unterminated string starting at %d: %s" % (start, sexp[start:]))


def tokenize_list(sexp: str, offset):
    c = sexp[offset]
    assert c == "("
    offset += 1

    offset = consume_whitespace(sexp, offset)

    r = []
    while offset < len(sexp):
        c = sexp[offset]

        if c == ")":
            return r, offset + 1

        t, offset = tokenize_sexp(sexp, offset)
        r.append(t)
        offset = consume_whitespace(sexp, offset)

    raise SyntaxError("missing )")


def tokenize_atom(sexp: str, offset):
    c = sexp[offset]
    if c in "\'\"":
        return tokenize_str(sexp, offset)

    start_offset = offset
    item, offset = consume_until_whitespace(sexp, offset)
    return Token(item, start_offset), offset


def tokenize_sexp(sexp: str, offset: int):
    offset = consume_whitespace(sexp, offset)

    if sexp[offset] == ")":
        raise SyntaxError("unexpected ) at %d" % offset)

    if sexp[offset] == "(":
        return tokenize_list(sexp, offset)

    return tokenize_atom(sexp, offset)


def tokenize_program(sexp: str):
    return tokenize_sexp(sexp, 0)[0]


def compile_to_sexp(program: str, keyword_to_int):
    "Read an expression from a string, yielding an SExp."
    tokenized = tokenize_program(program)
    return compile_token(tokenized, keyword_to_int)


def compile_to_blob(program: str):
    "Read an expression from a string, compiled to a binary blob."
    return compile_to_sexp(program).as_bin()


def dump(form, keywords=[], is_first_element=False):
    if form.is_list():
        return "(%s)" % ' '.join(str(dump(f, keywords, _ == 0)) for _, f in enumerate(form))

    if form.is_var():
        return "x%d" % form.var_index()

    if is_first_element and 0 <= form.as_int() < len(keywords):
        v = keywords[form.as_int()]
        if v != '.':
            return v

    if len(form.as_bytes()) > 4:
        return bytes_as_hex(form.as_bytes())

    return str(form.as_int())


def disassemble_sexp(form, keyword_from_int):
    return dump(form, keywords=keyword_from_int)


def disassemble_blob(blob, keyword_from_int):
    return disassemble_sexp(SExp.from_blob(blob), keyword_from_int)


def disassemble(item, keyword_from_int):
    if isinstance(item, SExp):
        return disassemble_sexp(item, keyword_from_int)
    if isinstance(item, bytes):
        return disassemble_blob(item, keyword_from_int)
    raise ValueError("expected SExp or bytes, got %s" % item)
