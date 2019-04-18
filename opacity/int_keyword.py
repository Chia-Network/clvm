# compiler

import binascii

from .Var import Var


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
            raise SyntaxError("invalid hex at %d: %s" % (offset, s))


def parse_as_var(s, offset):
    if s[:1].upper() == "X":
        try:
            return Var(int(s[1:]))
        except Exception:
            raise SyntaxError("invalid variable at %d: %s" % (offset, s))


def compile_atom(token, keyword_to_int):
    s = token.as_bytes().decode("utf8")
    c = s[0]
    if c in "\'\"":
        assert c == s[-1] and len(s) >= 2
        return token.as_bytes()[1:-1]

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
        return tokens

    r = []
    if not tokens[0].listp():
        keyword = keyword_to_int.get(tokens[0].as_bytes().decode("utf8").lower())
        if keyword:
            r.append(keyword)
            tokens = tokens[1:]

    for token in tokens:
        r.append(from_int_keyword_tokens(token, keyword_to_int))

    return r


def from_int_keyword_tokens(token, keyword_to_int):
    if token.listp():
        return compile_list(token, keyword_to_int)
    return compile_atom(token, keyword_to_int)


def to_int_keyword_tokens(form, keywords=[], is_first_element=False):
    to_sexp_f = form.__class__

    if form.listp():
        return to_sexp_f([to_int_keyword_tokens(f, keywords, _ == 0) for _, f in enumerate(form)])

    if form.is_var():
        return to_sexp_f(("x%d" % form.var_index()).encode("utf8"))

    if is_first_element:
        v = keywords.get(form.as_atom())
        if v is not None and v != '.':
            return v.encode("utf8")

    if len(form.as_bytes()) > 4:
        return to_sexp_f(("0x%s" % binascii.hexlify(form.as_bytes()).decode("utf8")).encode("utf8"))

    return to_sexp_f(("%d" % form.as_int()).encode("utf8"))
