# compiler
# with thanks to http://norvig.com/lispy.html

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


def parse_as_string(token):
    if len(token) > 1 and (token[:1], token[-1:]) in (("'", "'"), ('"', '"')):
        return token[1:-1].encode("utf8")


def parse_as_hex(token):
    if token[:2].upper() == "0X":
        return bytes_as_hex(binascii.unhexlify(token[2:]))


def parse_as_var(token):
    if token[:1].upper() == "X":
        return Var(int(token[1:]))


def tokenize(chars: str) -> list:
    "Convert a string of characters into a list of tokens."
    chars = chars.replace('(', ' ( ').replace(')', ' ) ')
    lines = chars.split("\n")
    uncommented_lines = [line.split(" ;", 1)[0] for line in lines]
    chars = ''.join(uncommented_lines)
    return chars.split()


def read_from_tokens(tokens: list):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF')
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop off ')'
        return L
    elif token == ')':
        raise SyntaxError('unexpected )')
    else:
        for c in [parse_as_string, parse_as_keyword, parse_as_int, parse_as_var, parse_as_hex]:
            v = c(token)
            if v is not None:
                return v
    raise ValueError("unparsable token: %s" % token)


def compile_text(program: str):
    "Read an expression from a string."
    return wrap_blobs(read_from_tokens(tokenize(program)))


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
