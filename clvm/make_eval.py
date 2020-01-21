# make the "eval" function for a vm with the given operators

import os

from .EvalError import EvalError

QUOTE_COST = 1
ARGS_COST = 1
DEFAULT_APPLY_COST = 1


def make_eval_f(operator_lookup, quote_kw, eval_kw, env_kw):

    CLVM_DISALLOW_E_OP = os.environ.get('CLVM_DISALLOW_E_OP')

    def eval_core(eval_f, form, env):
        if not form.listp():
            raise EvalError("not a list", form)

        if form.nullp():
            raise EvalError("eval cannot handle empty list", form)

        first_item = form.first()

        if first_item.listp():
            new_form = eval_f(eval_f, first_item, env)
            return eval_f(eval_f, new_form.first(), new_form.rest())

        f_index = first_item.as_atom()
        if f_index is None:
            raise EvalError("non-byte atom in first element of list", form)

        # special form QUOTE

        if f_index == quote_kw:
            if form.rest().nullp() or not form.rest().rest().nullp():
                raise EvalError("quote requires exactly 1 parameter", form)
            return form.rest().first()

        # TODO: rewrite with cons, rest, etc.
        args = form.to([eval_f(eval_f, _, env) for _ in form.rest().as_iter()])

        # keyword EVAL

        if f_index == eval_kw:
            if CLVM_DISALLOW_E_OP:
                if CLVM_DISALLOW_E_OP == "breakpoint":
                    print(form)
                    breakpoint()
                raise EvalError("e operator no longer supported", form)
            if args.rest().nullp() or not args.rest().rest().nullp():
                raise EvalError("eval requires 2 parameters", form)
            return eval_f(eval_f, args.first(), args.rest().first())

        # keyword ENV

        if f_index == env_kw:
            if form.nullp() or not form.rest().nullp():
                raise EvalError("env requires no parameters", form)
            return env

        # special form APPLY

        f = operator_lookup.get(f_index)
        if f:
            return f(args)

        raise EvalError("unimplemented operator", first_item)

    return eval_core


def make_eval_cost(operator_lookup, quote_kw, args_kw):

    def eval_core(eval_f, form, env, current_cost, max_cost):
        if not form.listp():
            raise EvalError("not a list", form)

        if form.nullp():
            raise EvalError("eval cannot handle empty list", form)

        first_item = form.first()

        if first_item.listp():
            new_cost, new_form = eval_f(eval_f, first_item, env, current_cost, max_cost)
            return eval_f(eval_f, new_form.first(), new_form.rest(), new_cost, max_cost)

        f_index = first_item.as_atom()
        if f_index is None:
            raise EvalError("non-byte atom in first element of list", form)

        # special form QUOTE

        if f_index == quote_kw:
            if form.rest().nullp() or not form.rest().rest().nullp():
                raise EvalError("quote requires exactly 1 parameter", form)
            return current_cost + QUOTE_COST, form.rest().first()

        # TODO: rewrite with cons, rest, etc.
        arg_list = []
        for _ in form.rest().as_iter():
            current_cost, r = eval_f(eval_f, _, env, current_cost, max_cost)
            arg_list.append(r)
        args = form.to(arg_list)

        # keyword ARGS

        if f_index == args_kw:
            if form.nullp() or not form.rest().nullp():
                raise EvalError("env requires no parameters", form)
            return current_cost + ARGS_COST, env

        # special form APPLY

        f = operator_lookup.get(f_index)
        if f:
            r = f(args)
            additional_cost = DEFAULT_APPLY_COST
            if isinstance(r, (tuple,)):
                additional_cost, r = r
            current_cost += additional_cost
            if max_cost and current_cost > max_cost:
                raise EvalError("cost exceeded", form)
            return current_cost, r

        raise EvalError("unimplemented operator", first_item)

    def eval_cost(eval_cost, form, env, current_cost=0, max_cost=1000000):
        return eval_core(eval_cost, form, env, current_cost, max_cost)

    return eval_cost
