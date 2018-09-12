# compiler

import binascii

from .serialize import unwrap_blob, wrap_blobs, Var
from .keywords import KEYWORD_FROM_INT, KEYWORD_TO_INT


def b2h(the_bytes):
    return binascii.hexlify(the_bytes).decode("utf8")


class Token(str):
    def __new__(self, s, offset):
        self = str.__new__(self, s)
        self._offset = offset
        return self


class bytes_as_hex(bytes):
    def __str__(self):
        return "0x%s" % b2h(self)

    def __repr__(self):
        return "0x%s" % b2h(self)


def parse_as_int(token):
    try:
        v = int(token)
        byte_count = (v.bit_length() + 7) >> 3
        return v.to_bytes(byte_count, "big", signed=True)
    except (ValueError, TypeError):
        pass


def parse_as_keyword(token):
    v = KEYWORD_TO_INT.get(token.lower())
    if v is not None:
        return v


def parse_as_hex(token):
    if token[:2].upper() == "0X":
        try:
            return bytes_as_hex(binascii.unhexlify(token[2:]))
        except Exception:
            raise SyntaxError("invalid hex at %d: %s" % (token._offset, token))


def parse_as_var(token):
    if token[:1].upper() == "X":
        try:
            return Var(int(token[1:]))
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


def compile_atom(token):
    c = token[0]
    if c in "\'\"":
        assert c == token[-1] and len(token) >= 2
        return token[1:-1].encode("utf8")

    for f in [parse_as_int, parse_as_var, parse_as_hex]:
        v = f(token)
        if v is not None:
            return v
    raise SyntaxError("can't parse %s at %d" % (token, token._offset))


def compile_list(tokens):
    if len(tokens) == 0:
        return []

    r = []
    if isinstance(tokens[0], str):
        keyword = KEYWORD_TO_INT.get(tokens[0].lower())
        if keyword:
            r.append(keyword)
            tokens = tokens[1:]

    for token in tokens:
        r.append(compile_token(token))

    return r


def compile_token(token):
    if isinstance(token, str):
        return compile_atom(token)
    return compile_list(token)


def expand_macro(tokens, macro_info):

    def expand(template, lookup):
        if isinstance(template, list):
            return [expand(_, lookup) for _ in template]
        return lookup.get(template, template)

    lookup = dict(zip(macro_info["declaration"][1:], tokens[1:]))

    return expand(macro_info["template"], lookup)


def compile_macro(tokens):
    # (macro (macroname var0 var1 ...) (expansion))
    if len(tokens) != 3 or any(not isinstance(_, list) for _ in tokens[1:]):
        raise SyntaxError("macro requires exactly two list parameters")

    macro_declaration = tokens[1]
    macro_name = tokens[1][0]
    return macro_name, {"template": tokens[2], "declaration": macro_declaration}


def macro_expansion(token, macros):
    if isinstance(token, list):
        if len(token) > 0:
            if not isinstance(token[0], list):
                macro = macros.get(token[0])
                if macro:
                    return expand_macro(token, macro)
        return [macro_expansion(_, macros) for _ in token]
    return token


def parse_macro_def(token, macros):
    if not isinstance(token, list):
        raise SyntaxError("macro expected, got %s" % token)
    name, macro = compile_macro(token)
    if name in macros:
        raise SyntaxError("macro %s redefined" % name)
    macros[name] = macro


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


def consume_to_eol(sexp:str, offset: int):
    return offset


def tokenize_sexp(sexp: str, offset: int):
    offset = consume_whitespace(sexp, offset)

    if sexp[offset] == ")":
        raise SyntaxError("unexpected ) at %d" % offset)

    if sexp[offset] == "(":
        return tokenize_list(sexp, offset)

    return tokenize_atom(sexp, offset)


def tokenize_program(sexp: str):
    return tokenize_sexp(sexp, 0)[0]


def compile_text(program: str, macros={}):
    "Read an expression from a string."
    tokenized = tokenize_program(program)
    tokenized = macro_expansion(tokenized, macros)
    compiled = compile_token(tokenized)
    return wrap_blobs(compiled)


def parse_macros(program: str, macros: dict=None):
    if macros is None:
        macros = {}
    for macro_def in tokenize_program(program):
        parse_macro_def(macro_def, macros)
    return macros


def disassemble_unwrapped(form):

    if isinstance(form, list):
        return "(%s)" % ' '.join(str(disassemble_unwrapped(_)) for _ in form)

    if isinstance(form, Var):
        return "x%d" % form.index

    if isinstance(form, int):
        if form < len(KEYWORD_FROM_INT):
            return KEYWORD_FROM_INT[form]

    if len(form) > 4:
        return bytes_as_hex(form)

    return str(int.from_bytes(form, "big", signed=True))


def disassemble(blob):
    return disassemble_unwrapped(unwrap_blob(blob))
