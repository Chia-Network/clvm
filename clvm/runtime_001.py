from .SExp import SExp

from .make_eval_rs import make_run_program
from .operators import (
    KEYWORD_TO_ATOM,
    OPERATOR_LOOKUP,
)
from .operators import KEYWORD_FROM_ATOM  # noqa

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
    run_program = make_run_program(operator_lookup, quote_kw, args_kw)

    r, cycles = run_program(program, args, pre_eval_f=pre_eval_f, max_cost=max_cost)
    return cycles, args.to(r)
