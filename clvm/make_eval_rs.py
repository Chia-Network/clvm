# make the "eval" function for a vm with the given operators

import io

from clvm_rust import do_eval, PySExp as Node

from .SExp import SExp

from .serialize import sexp_from_stream, sexp_to_stream
from .EvalError import EvalError


def sexp_to_blob(sexp):
    f = io.BytesIO()
    sexp_to_stream(sexp, f)
    return f.getvalue()


def sexp_from_blob(blob, to_sexp_f):
    f = io.BytesIO(bytes(blob))
    return sexp_from_stream(f, to_sexp_f)


def run_program(
    form,
    env,
    quote_kw,
    operator_lookup,
    max_cost=0,
    pre_eval_op=None,
    pre_eval_f=None,
):

    def internal_operator(operator_blob, args_blob):
        operator = sexp_from_blob(operator_blob, SExp.to)
        args = sexp_from_blob(args_blob, SExp.to)
        f = operator_lookup.get(operator.as_atom())
        r = f(args)
        return sexp_to_blob(r)

    form_blob = sexp_to_blob(form)
    env_blob = sexp_to_blob(env)
    error, r_blob, cycles = do_eval(
        form_blob, env_blob, internal_operator, pre_eval_f, quote_kw[0], args_kw[0])
    r = sexp_from_blob(bytes(r_blob), SExp.to)
    if error:
        raise EvalError(error, r)
    return cycles, r
