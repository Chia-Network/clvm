# make the "eval" function for a vm with the given operators

from . import casts

from .EvalError import EvalError

QUOTE_COST = 1
ARGS_COST = 1
DEFAULT_APPLY_COST = 1


class Eval:
    def __init__(
        self, operator_lookup, quote_kw, args_kw, pre_eval_f=None, post_eval_f=None
    ):
        self.operator_lookup = operator_lookup
        self.pre_eval_f = pre_eval_f
        self.post_eval_f = post_eval_f
        self.quote_kw = quote_kw
        self.args_kw = args_kw

    def __call__(self, sexp, env, max_cost=None):
        return self.eval(sexp, env, current_cost=0, max_cost=max_cost)

    def eval_atom(self, sexp, env):
        node_index = casts.int_from_bytes(sexp.as_atom())
        cost = 1
        while node_index > 1:
            if node_index & 1:
                env = env.rest()
            else:
                env = env.first()
            node_index >>= 1
            cost += 1
        return cost, env

    def eval(self, sexp, env, current_cost, max_cost):
        if not sexp.listp():
            return self.eval_atom(sexp, env)

        if sexp.nullp():
            raise EvalError("eval cannot handle empty list", sexp)

        first_item = sexp.first()

        if first_item.listp():
            new_cost, new_sexp = self.eval(first_item, env, current_cost, max_cost)
            return self.eval(new_sexp.first(), new_sexp.rest(), new_cost, max_cost)

        f_index = first_item.as_atom()
        if f_index is None:
            raise EvalError("non-byte atom in first element of list", sexp)

        # special form QUOTE

        if f_index == self.quote_kw:
            if sexp.rest().nullp() or not sexp.rest().rest().nullp():
                raise EvalError("quote requires exactly 1 parameter", sexp)
            return current_cost + QUOTE_COST, sexp.rest().first()

        # keyword ARGS

        if f_index == self.args_kw:
            if sexp.nullp() or not sexp.rest().nullp():
                raise EvalError("env requires no parameters", sexp)
            return current_cost + ARGS_COST, env

        # TODO: rewrite with cons, rest, etc.
        arg_list = []
        for _ in sexp.rest().as_iter():
            current_cost, r = self.eval(_, env, current_cost, max_cost)
            arg_list.append(r)
        args = sexp.to(arg_list)

        # special form APPLY

        current_cost, r = self.apply(f_index, args, current_cost, max_cost)
        if max_cost and current_cost > max_cost:
            raise EvalError("cost exceeded", sexp)
        return current_cost, r

    def apply(self, operator, args, current_cost, max_cost):
        f = self.operator_lookup.get(operator)
        if f:
            if getattr(f, "needs_eval", 0):
                r = f(args, self)
            else:
                r = f(args)
            additional_cost = DEFAULT_APPLY_COST
            if isinstance(r, (tuple,)):
                additional_cost, r = r
            current_cost += additional_cost
            return current_cost, r

        raise EvalError("unimplemented operator", args.to(operator))
