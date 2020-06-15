from .SExp import SExp

from .operators import (
    KEYWORD_TO_ATOM,
    OPERATOR_LOOKUP,
)
from .operators import KEYWORD_FROM_ATOM  # noqa

from .run_program import run_program as default_run_program

to_sexp_f = SExp.to  # noqa


def run_program(
    program,
    args,
    quote_kw=KEYWORD_TO_ATOM["q"],
    args_kw=KEYWORD_TO_ATOM["a"],
    operator_lookup=OPERATOR_LOOKUP,
    max_cost=None,
    pre_eval_f=None,
):
    def my_pre_eval_op(op_stack, value_stack):
        v = value_stack[-1]
        context = pre_eval_f(v.first(), v.rest())
        if callable(context):

            def invoke_context_op(op_stack, value_stack):
                context(value_stack[-1])
                return 0

            op_stack.append(invoke_context_op)

    if pre_eval_f is None:
        pre_eval_op = None
    else:
        pre_eval_op = my_pre_eval_op

    return default_run_program(
        program, args, quote_kw, args_kw, operator_lookup, max_cost, pre_eval_op
    )
