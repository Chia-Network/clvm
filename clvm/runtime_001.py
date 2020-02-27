import io

from . import core_ops, more_ops

from .Eval import Eval
from .casts import (
    int_from_bytes,
    int_to_bytes,
    bls12_381_from_bytes,
    bls12_381_to_bytes,
    bls12_381_generator,
)
from .op_utils import operators_for_module
from .serialize import sexp_to_stream
from .subclass_sexp import subclass_sexp


class mixin:
    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        if isinstance(v, bls12_381_generator.__class__):
            v = bls12_381_to_bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def as_bytes(self):
        return self.as_atom()

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    def as_bls12_381(self):
        return bls12_381_from_bytes(self.as_atom())


to_sexp_f = subclass_sexp(mixin, (bytes,), false=b"")


KEYWORDS = (
    ". q e a i c f r l x = sha256 + - * . "
    ". . point_add pubkey_for_exp . sha256tree > >s"
).split()

KEYWORD_FROM_ATOM = {int_to_bytes(k): v for k, v in enumerate(KEYWORDS)}
KEYWORD_TO_ATOM = {v: k for k, v in KEYWORD_FROM_ATOM.items()}

OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
    "i": "if",
    "c": "cons",
    "f": "first",
    "r": "rest",
    "l": "listp",
    "x": "raise",
    "=": "eq",
    ">": "gr",
    ">s": "gr_bytes",
}


OPERATOR_LOOKUP = operators_for_module(KEYWORD_TO_ATOM, core_ops, OP_REWRITE)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_ATOM, more_ops, OP_REWRITE))


def run_program(
    program,
    args,
    quote_kw=KEYWORD_TO_ATOM["q"],
    args_kw=KEYWORD_TO_ATOM["a"],
    operator_lookup=None,
    max_cost=None,
    pre_eval_f=None,
    post_eval_f=None,
):

    if operator_lookup is None:
        operator_lookup = OPERATOR_LOOKUP

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
