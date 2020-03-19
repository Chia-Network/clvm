import io

from . import core_ops, more_ops

from .casts import (
    int_from_bytes,
    int_to_bytes,
    bls12_381_from_bytes,
    bls12_381_to_bytes,
    bls12_381_generator,
)
from .op_utils import operators_for_module
from .run_program import run_program as default_run_program
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

    return default_run_program(program, args, quote_kw, args_kw, operator_lookup, max_cost, pre_eval_op)
