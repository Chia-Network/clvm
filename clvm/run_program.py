from .Eval import Eval


def make_run_program(operator_lookup, quote_kw, args_kw):

    def run_program(
        program,
        args,
        quote_kw=quote_kw,
        args_kw=args_kw,
        operator_lookup=operator_lookup,
        max_cost=None,
        pre_eval_f=None,
        post_eval_f=None,
    ):

        eval_class = Eval
        if pre_eval_f or post_eval_f:

            class WrappedEval(Eval):
                def eval(self, sexp, env, current_cost, max_cost):
                    context = None
                    if pre_eval_f:
                        context = pre_eval_f(sexp, env, current_cost, max_cost)
                    try:
                        r = super().eval(sexp, env, current_cost, max_cost)
                    except Exception as ex:
                        r = (0, sexp.to(("FAIL: %s" % str(ex)).encode("utf8")))
                        raise
                    finally:
                        if post_eval_f:
                            post_eval_f(context, r)
                    return r

            eval_class = WrappedEval

        eval = eval_class(operator_lookup, quote_kw, args_kw)

        return eval(program, args, max_cost=max_cost)

    return run_program
