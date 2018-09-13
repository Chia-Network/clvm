import hashlib

from .keywords import KEYWORD_TO_INT

from .serialize import Var, unwrap_blob


def int_to_bytes(v):
    byte_count = (v.bit_length() + 7) >> 3
    if byte_count > 16:
        v = 0
    if v == 0:
        return b''
    return v.to_bytes(byte_count, "big", signed=True)


def int_from_bytes(blob):
    size = len(blob)
    if size == 0 or size > 16:
        return 0
    return int.from_bytes(blob, "big", signed=True)


def has_unbound_values(items):
    return any(not isinstance(_, bytes) for _ in items)


def as_ints(items):
    return (int_from_bytes(_) for _ in items)


def do_implicit_and(form, bindings):
    items = [reduce(_, bindings) for _ in form]
    if b'' in items:
        return b''
    items = [_ for _ in items if not isinstance(_, bytes)]
    if has_unbound_values(items):
        return items
    return int_to_bytes(1 if all(_ != b'' for _ in items) else 0)


def do_choose1(form, bindings):
    if len(form) < 2:
        return b''
    choice = reduce(form[1], bindings)
    if has_unbound_values([choice]):
        return form
    choice = int_from_bytes(choice)
    choices = form[2:]
    if 0 <= choice < len(choices):
        chosen_form = choices[choice]
        return reduce(chosen_form, bindings)
    return b''


def do_add(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return [form[0]] + items
    return int_to_bytes(sum(as_ints(items)) & ((1 << 128) - 1))


def do_apply(form, bindings):
    if len(form) != 3:
        return int_to_bytes(1)
    items = [reduce(_, bindings) for _ in form[1:3]]
    if has_unbound_values(items):
        return [form[0]] + items
    truncate_count, wrapped_form = items
    new_bindings = bindings
    v = int_from_bytes(truncate_count)
    if v > 0:
        new_bindings = new_bindings[v:]
    return reduce(unwrap_blob(wrapped_form), new_bindings)


def do_nop(form, bindings):
    return form


def do_sha256(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return [form[0]] + items
    h = hashlib.sha256()
    for _ in items:
        h.update(_)
    return h.digest()


def do_equal(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    if has_unbound_values(items):
        return [form[0]] + items
    if len(items) == 0:
        return int_to_bytes(1)
    return int_to_bytes(0 if any(_ != items[0] for _ in items[1:]) else 1)


def do_reduce(form, bindings):
    items = [reduce(_, bindings) for _ in form[1:]]
    new_form = unwrap_blob(items[0])
    new_bindings = unwrap_blob(items[1])
    return reduce(new_form, new_bindings)


def do_recursive_reduce(form, bindings):
    return form[:1] + [reduce(_, bindings) for _ in form[1:]]


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


def reduce(form, bindings):
    if isinstance(form, Var):
        index = form.index
        if 0 <= index < len(bindings):
            return bindings[index]
        return form

    if isinstance(form, list):
        if len(form) > 0:
            if isinstance(form[0], list):
                return do_implicit_and(form, bindings)
            f = REDUCE_LOOKUP.get(form[0], do_implicit_and)
            return f(form, bindings)
        return b''

    return form
