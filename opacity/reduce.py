import hashlib

from .casts import bls12_381_from_bytes, bls12_381_to_bytes
from .ecdsa.bls12_381 import bls12_381_generator
from .keywords import KEYWORD_TO_INT

from .SExp import SExp


S_False = SExp(0)
S_True = SExp(1)


def has_unbound_values(items):
    return any(not _.is_bytes() for _ in items)


def do_implicit_and(form, bindings):
    items = [reduce(_, bindings) for _ in form]
    if S_False in items:
        return S_False
    items = [_ for _ in items if not _.is_bytes()]
    if has_unbound_values(items):
        return SExp(items)
    return S_True if all(_ != S_False for _ in items) else S_False


def do_pubkey_for_exp(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return SExp([form[0], *items])

    def blob_for_item(_):
        try:
            return bls12_381_to_bytes(bls12_381_generator * _.as_int())
        except Exception as ex:
            return b''

    return SExp([blob_for_item(_) for _ in form[1:]])


def do_point_add(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return SExp([form[0], *items])
    p = bls12_381_from_bytes(form[1].as_bytes())
    for _ in form[2:]:
        p += bls12_381_from_bytes(_.as_bytes())
    return SExp(bls12_381_to_bytes(p))


def do_add(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return SExp([form[0], *items])
    return SExp(sum(_.as_int() for _ in items) & ((1 << 128) - 1))


def do_sha256(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return SExp([form[0], *items])
    h = hashlib.sha256()
    for _ in items:
        h.update(_.as_bytes())
    return SExp(h.digest())


def do_equal(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return SExp([form[0], *items])
    if len(items) == 0:
        return SExp(1)
    return SExp(0 if any(_ != items[0] for _ in items[1:]) else 1)


def do_choose1(form, bindings):
    if len(form) < 2:
        return S_False
    choice = reduce(form[1], bindings)
    if has_unbound_values([choice]):
        return form
    choice = choice.as_int()
    choices = form[2:]
    if 0 <= choice < len(choices):
        chosen_form = choices[choice]
        return reduce(chosen_form, bindings)
    return S_False


def do_reduce(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    new_form = SExp.from_blob(items[0].as_bytes())
    new_bindings = SExp.from_blob(items[1].as_bytes())
    return reduce(new_form, new_bindings)


def do_recursive_reduce(form, bindings):
    return SExp(form.as_list()[:1] + [reduce(_, bindings) for _ in form[1:]])


def build_reduce_lookup(keyword_to_int):
    remap = {
        "+": do_add,
    }
    g = globals()
    d = dict()
    for k, i in keyword_to_int.items():
        if k in remap:
            d[i] = remap[k]
        else:
            d[i] = g.get("do_%s" % k, do_recursive_reduce)
    return d


REDUCE_LOOKUP = build_reduce_lookup(KEYWORD_TO_INT)


def reduce(form: SExp, bindings: SExp):
    # a lazy trick to help tests
    bindings = SExp(bindings)

    if form.is_var():
        index = form.var_index()
        if 0 <= index < len(bindings.as_list() or []):
            return bindings.as_list()[index]
        return form

    if form.is_list():
        if len(form) > 0:
            if form[0].is_list():
                return do_implicit_and(form, bindings)
            f = REDUCE_LOOKUP.get(form[0].as_int(), do_implicit_and)
            return f(form, bindings)
        return SExp(0)

    return form
