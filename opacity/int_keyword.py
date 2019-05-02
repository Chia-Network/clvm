# compiler

import binascii

from clvm.casts import int_from_bytes

from .Var import Var
from .reader import tokenize


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def parse_as_int(s, offset):
    try:
        v = int(s)
        return v
    except (ValueError, TypeError):
        pass


def parse_as_hex(s, offset):
    if s[:2].upper() == "0X":
        try:
            return bytes_as_hex(binascii.unhexlify(s[2:]))
        except Exception:
            raise SyntaxError("invalid hex at %s: %s" % (offset, s))


def parse_as_var(s, offset):
    if s[:1].upper() == "X":
        try:
            return Var(int(s[1:]))
        except Exception:
            raise SyntaxError("invalid variable at %s: %s" % (offset, s))


def compile_atom(token, keyword_to_int):
    s = token.as_atom()
    c = s[0]
    if c in "\'\"":
        assert c == s[-1] and len(s) >= 2
        return s[1:-1].encode("utf8")

    if c == '#':
        keyword = s[1:].lower()
        keyword_id = keyword_to_int.get(keyword)
        if keyword_id is None:
            raise SyntaxError("unknown keyword: %s" % keyword)
        return keyword_id

    for f in [parse_as_int, parse_as_var, parse_as_hex]:
        v = f(s, token._offset)
        if v is not None:
            return v
    raise SyntaxError("can't parse %s at %d" % (s, token._offset))


def compile_list(tokens, keyword_to_int):
    if tokens.nullp():
        return []

    r = []
    if not tokens.first().listp():
        keyword = keyword_to_int.get(tokens.first().as_atom().lower())
        if keyword:
            r.append(keyword)
            tokens = tokens.rest()

    for token in tokens.as_iter():
        r.append(from_int_keyword_tokens(token, keyword_to_int))

    return r


def from_int_keyword_tokens(token, keyword_to_int):
    if token.listp():
        return compile_list(token, keyword_to_int)
    return compile_atom(token, keyword_to_int)


def to_int_keyword_tokens(form, keywords=[], is_first_element=False):
    to_sexp_f = tokenize

    if form.listp():
        return to_sexp_f([to_int_keyword_tokens(f, keywords, _ == 0) for _, f in enumerate(form.as_iter())])

    as_atom = form.as_atom()
    if isinstance(as_atom, Var):
        return to_sexp_f(("x%d" % as_atom.index))

    if is_first_element:
        v = keywords.get(as_atom)
        if v is not None and v != '.':
            return v

    if len(as_atom) > 4:
        return to_sexp_f(("0x%s" % binascii.hexlify(as_atom).decode("utf8")))

    return to_sexp_f(("%d" % int_from_bytes(as_atom)))
