from .keywords import KEYWORD_TO_INT
from .operators import all_operators

from .SExp import SExp


S_False = SExp(0)
S_True = SExp(1)


def has_unbound_values(items):
    return any(not _.is_bytes() for _ in items)


def do_choose1(form, bindings, reduce_f):
    if len(form) < 2:
        return S_False
    choice = reduce_f(form[1], bindings, reduce_f)
    if has_unbound_values([choice]):
        return form
    choice = choice.as_int()
    choices = form[2:]
    if 0 <= choice < len(choices):
        chosen_form = choices[choice]
        return reduce_f(chosen_form, bindings, reduce_f)
    return S_False


QUOTE_KEYWORD = KEYWORD_TO_INT["quote"]
UNQUOTE_KEYWORD = KEYWORD_TO_INT["unquote"]


def quote(form, bindings, reduce_f, level):
    if form.is_list() and len(form) > 0:
        op = form[0].as_int()
        if op == QUOTE_KEYWORD:
            level += 1
        if op == UNQUOTE_KEYWORD:
            level -= 1
            if level == 0:
                if len(form) > 1:
                    return reduce_f(form[1], bindings, reduce_f)
        return SExp([quote(_, bindings, reduce_f, level) for _ in form])

    return form


def do_quote(form, bindings, reduce_f):
    if len(form) > 1:
        return quote(form[1], bindings, reduce_f, 1)
    return S_False


def do_wrap(form, bindings, reduce_f):
    if len(form) < 2:
        return S_False
    item = reduce_f(form[1], bindings, reduce_f)
    return SExp(item.as_bin())


def do_reduce(form, bindings, reduce_f):
    if len(form) < 2:
        return S_False
    new_form = reduce_f(form[1], bindings, reduce_f)
    if len(form) > 2:
        new_bindings = reduce_f(form[2], bindings, reduce_f)
    else:
        new_bindings = SExp([])
    return reduce_f(new_form, new_bindings, reduce_f)


def do_recursive_reduce(form, bindings, reduce_f):
    return SExp(form.as_list()[:1] + [reduce_f(_, bindings, reduce_f) for _ in form[1:]])


def build_reduce_lookup(remap, keyword_to_int):
    g = globals()
    d = all_operators(remap, keyword_to_int)
    for k, i in keyword_to_int.items():
        if k in remap:
            k = remap[k]
        f = g.get("do_%s" % k)
        if f:
            d[i] = f

    return d


REDUCE_LOOKUP = build_reduce_lookup({"+": "add"}, KEYWORD_TO_INT)


def reduce(form: SExp, bindings: SExp, reduce_f=None):
    # a lazy trick to help tests
    bindings = SExp(bindings)

    reduce_f = reduce_f or reduce

    if form.is_var():
        index = form.var_index()
        if 0 <= index < len(bindings.as_list() or []):
            return bindings.as_list()[index]
        return form

    if form.is_list():
        if len(form) > 0:
            if form[0].is_list():
                new_form = SExp([KEYWORD_TO_INT["and"]] + form.as_list())
                return reduce_f(new_form, bindings, reduce_f)
            f = REDUCE_LOOKUP.get(form[0].as_int(), do_recursive_reduce)
            if f:
                return f(form, bindings, reduce_f)

            return f(form, bindings, reduce_f)
        return S_False

    return form
