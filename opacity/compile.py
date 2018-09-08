# compiler

import binascii

from .serialize import unwrap_blob, wrap_blobs, Var
from .keywords import KEYWORD_FROM_INT, KEYWORD_TO_INT


def b2h(the_bytes):
    return binascii.hexlify(the_bytes).decode("utf8")


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
            raise SyntaxError("invalid hex: %s" % token[2:])


def parse_as_var(token):
    if token[:1].upper() == "X":
        try:
            return Var(int(token[1:]))
        except Exception:
            raise SyntaxError("invalid int: %s" % token[1:])


def consume_whitespace(sexp: str, offset):
    while offset < len(sexp) and sexp[offset].isspace():
        offset += 1
    return offset


def consume_until_whitespace(sexp: str, offset):
    start = offset
    while offset < len(sexp) and not sexp[offset].isspace() and sexp[offset] != ")":
        offset += 1
    return sexp[start:offset], offset


def compile_str(sexp: str, offset):
    start = offset
    initial_c = sexp[start]
    offset += 1
    while offset < len(sexp) and sexp[offset] != initial_c:
        offset += 1
    if offset < len(sexp):
        return sexp[start+1:offset].encode("utf8"), offset + 1
    raise SyntaxError("unterminated string starting at %d: %s" % (start, sexp[start:]))


def compile_atom(sexp: str, offset):
    c = sexp[offset]
    if c in "\'\"":
        return compile_str(sexp, offset)

    item, offset = consume_until_whitespace(sexp, offset)
    for f in [parse_as_int, parse_as_var, parse_as_hex, parse_as_keyword]:
        v = f(item)
        if v is not None:
            return v, offset
    raise SyntaxError("can't parse %s at %d" % (item, offset))


def compile_list(sexp: str, offset):
    c = sexp[offset]
    assert c == "("
    offset += 1

    offset = consume_whitespace(sexp, offset)

    r = []
    while offset < len(sexp):
        c = sexp[offset]

        if c == ")":
            return r, offset + 1

        t, offset = compile_sexp(sexp, offset)
        r.append(t)
        offset = consume_whitespace(sexp, offset)

    raise SyntaxError("missing )")


def compile_sexp(sexp: str, offset=0):
    offset = consume_whitespace(sexp, offset)

    if sexp[offset] == "(":
        return compile_list(sexp, offset)

    return compile_atom(sexp, offset)


def compile_text(program: str):
    "Read an expression from a string."
    return wrap_blobs(compile_sexp(program)[0])


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
