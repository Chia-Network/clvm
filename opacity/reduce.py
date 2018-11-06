import dataclasses

from .keywords import KEYWORD_TO_INT
from .operators import all_operators, has_unbound_values

from .SExp import SExp


S_False = SExp(0)
S_True = SExp(1)


def do_choose1(form, context):
    if len(form) < 2:
        return S_False
    choice = context.reduce_f(form[1], context)
    if has_unbound_values([choice]):
        return form
    choice = choice.as_int()
    choices = form[2:]
    if 0 <= choice < len(choices):
        chosen_form = choices[choice]
        return context.reduce_f(chosen_form, context)
    return S_False


QUOTE_KEYWORD = KEYWORD_TO_INT["quote"]
UNQUOTE_KEYWORD = KEYWORD_TO_INT["unquote"]


def quote(form, context, level):
    if form.is_list() and len(form) > 0:
        op = form[0].as_int()
        if op == QUOTE_KEYWORD:
            level += 1
        if op == UNQUOTE_KEYWORD:
            level -= 1
            if level == 0:
                if len(form) > 1:
                    return context.reduce_f(form[1], context)
        return SExp([quote(_, context, level) for _ in form])

    return form


def do_quote(form, context):
    if len(form) > 1:
        return quote(form[1], context, 1)
    return S_False


def do_wrap(form, context):
    if len(form) < 2:
        return S_False
    item = context.reduce_f(form[1], context)
    return SExp(item.as_bin())


def do_reduce(form, context):
    if len(form) < 2:
        return S_False
    new_form = context.reduce_f(form[1], context)
    if len(form) > 2:
        new_bindings = context.reduce_f(form[2], context)
        if new_bindings.is_list():
            new_context = dataclasses.replace(context, bindings=new_bindings)
        else:
            new_context = dataclasses.replace(context, bindings=SExp([]))
    else:
        new_context = dataclasses.replace(context, bindings=SExp([]))
    return context.reduce_f(new_form, new_context)


def do_recursive_reduce(form, context):
    return SExp(form.as_list()[:1] + [context.reduce_f(_, context) for _ in form[1:]])


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


REDUCE_LOOKUP = build_reduce_lookup({"+": "add", "*": "multiply", "-": "subtract"}, KEYWORD_TO_INT)


DEFAULT_OPERATOR = KEYWORD_TO_INT["and"]


def apply_f(form, context):
    f = context.apply_lookup.get(form[0].as_int())
    if f:
        return f(form, context)
    return do_recursive_reduce(form, context)


def reduce_bytes(form, context):
    return form


def reduce_var(form, context):
    index = form.var_index()
    if context.bindings.is_list() and 0 <= index < len(context.bindings):
        return context.bindings[index]
    return form


def reduce_list(form, context):
    if len(form) > 0:
        if form[0].is_list():
            form = SExp([context.default_operator] + form.as_list())
        return apply_f(form, context)
    return S_False


@dataclasses.dataclass
class ReduceContext:
    reduce_f: None
    reduce_var: None
    default_operator: int
    apply_lookup: dict
    apply_default: None
    reduce_bytes: None = reduce_bytes
    bindings: SExp = SExp([])
    reduce_list: None = reduce_list
    apply_f: None = apply_f


def default_reduce_f(form: SExp, context: ReduceContext):
    if form.is_bytes():
        return context.reduce_bytes(form, context)

    if form.is_var():
        return context.reduce_var(form, context)

    return context.reduce_list(form, context)


def reduce(form: SExp, bindings: SExp, reduce_f=None):
    # a lazy trick to help tests
    bindings = SExp(bindings)

    reduce_f = reduce_f or default_reduce_f
    context = ReduceContext(
        reduce_f=reduce_f, reduce_var=reduce_var, bindings=bindings, default_operator=DEFAULT_OPERATOR,
        apply_lookup=REDUCE_LOOKUP, apply_default=do_recursive_reduce)
    return reduce_f(form, context)
