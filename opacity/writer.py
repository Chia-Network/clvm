# writer


def write_tokens(sexp):
    if sexp.listp():
        return "(%s)" % ' '.join(write_tokens(_) for _ in sexp)
    return sexp.as_atom().decode("utf8")
