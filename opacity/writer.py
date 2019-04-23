# writer


def write_tokens(sexp):
    if sexp.listp():
        return "(%s)" % ' '.join(write_tokens(_) for _ in sexp.as_iter())
    return sexp.as_atom()
