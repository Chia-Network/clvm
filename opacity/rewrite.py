from .SExp import SExp

from .keywords import KEYWORD_TO_INT

from .ReduceError import ReduceError

ENV_RAW_KEYWORD = KEYWORD_TO_INT["env_raw"]
GET_RAW_KEYWORD = KEYWORD_TO_INT["get"]
QUOTE_KEYWORD = KEYWORD_TO_INT["quote"]
REDUCE_KEYWORD = KEYWORD_TO_INT["reduce"]


def contains_no_free_variables(form):
    if form.is_list():
        first_item = form[0]
        if first_item.is_list():
            return False
        if first_item == ENV_RAW_KEYWORD:
            return False
        if first_item == QUOTE_KEYWORD:
            return True
        if first_item == REDUCE_KEYWORD:
            if len(form) > 2:
                return contains_no_free_variables(form[2])
        return all(contains_no_free_variables(_) for _ in form[1:])

    if form.is_var():
        return False

    return True


def do_rewrite(self, reduce, form: SExp, derived_operators: dict):
    if form.is_var():
        return SExp([GET_RAW_KEYWORD, [ENV_RAW_KEYWORD], form.var_index()])

    if form.is_bytes():
        return SExp([QUOTE_KEYWORD, form])

    if len(form) == 0:
        return SExp([QUOTE_KEYWORD, form])

    first_item = form[0]

    if first_item.is_list():
        new_env = form[1:]
        new_form = reduce(first_item, new_env)
        return self(self, reduce, new_form, derived_operators)

    if first_item.is_bytes():
        f_index = first_item.as_int()

        if f_index in (QUOTE_KEYWORD, ENV_RAW_KEYWORD):
            return form

        args = [self(self, reduce, _, derived_operators) for _ in form[1:]]

        if f_index == REDUCE_KEYWORD and len(args) == 1:
            if args[0].is_list():
                r_first = args[0][0]
                if r_first.as_int() == QUOTE_KEYWORD:
                    return args[0][1]

        new_form = SExp([first_item] + args)

        if contains_no_free_variables(new_form):
            empty_env = SExp([])
            new_form = reduce(form, empty_env)
            return SExp([QUOTE_KEYWORD, new_form])

        f = derived_operators.get(f_index)
        if f:
            new_form = f(self, reduce, new_form, derived_operators)
            new_form = self(self, reduce, new_form, derived_operators)
        return new_form

    raise ReduceError("don't know how to handle variable in position 0")
