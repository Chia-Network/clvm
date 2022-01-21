from typing import Callable, Optional, Tuple

try:
    import clvm_rs
except ImportError:
    clvm_rs = None

from . import core_ops, more_ops
from .chainable_multi_op_fn import ChainableMultiOpFn
from .handle_unknown_op import (
    handle_unknown_op_softfork_ready,
    handle_unknown_op_strict,
)
from .run_program import _run_program
from .types import CLVMObjectType, ConversionFn, MultiOpFn, OperatorDict


OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "div",
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


def op_table_for_module(mod):

    # python-implemented operators don't take `max_cost` and rust-implemented operators do
    # So we make the `max_cost` operator optional with this trick
    # TODO: have python-implemented ops also take `max_cost` and unify the API.

    def elide_max_cost(f):
        def inner_op(sexp, max_cost=None):
            try:
                return f(sexp, max_cost)
            except TypeError:
                return f(sexp)

        return inner_op

    return {
        k: elide_max_cost(v) for k, v in mod.__dict__.items() if k.startswith("op_")
    }


def op_imp_table_for_backend(backend):
    if backend is None and clvm_rs:
        backend = "native"

    if backend == "native":
        if clvm_rs is None:
            raise RuntimeError("native backend not installed")
        return clvm_rs.native_opcodes_dict()

    table = {}
    table.update(op_table_for_module(core_ops))
    table.update(op_table_for_module(more_ops))
    return table


def op_atom_to_imp_table(op_imp_table, keyword_to_atom, op_rewrite=OP_REWRITE):
    op_atom_to_imp_table = {}
    for op, bytecode in keyword_to_atom.items():
        op_name = "op_%s" % op_rewrite.get(op, op)
        op_f = op_imp_table.get(op_name)
        if op_f:
            op_atom_to_imp_table[bytecode] = op_f
    return op_atom_to_imp_table


def opcode_table_for_backend(keyword_to_atom, backend):
    op_imp_table = op_imp_table_for_backend(backend)
    return op_atom_to_imp_table(op_imp_table, keyword_to_atom)


class Dialect:
    def __init__(
        self,
        quote_kw: bytes,
        apply_kw: bytes,
        multi_op_fn: MultiOpFn,
        to_python: ConversionFn,
    ):
        self.quote_kw = quote_kw
        self.apply_kw = apply_kw
        self.opcode_lookup = dict()
        self.multi_op_fn = ChainableMultiOpFn(self.opcode_lookup, multi_op_fn)
        self.to_python = to_python

    def update(self, d: OperatorDict) -> None:
        self.opcode_lookup.update(d)

    def clear(self) -> None:
        self.opcode_lookup.clear()

    def run_program(
        self,
        program: CLVMObjectType,
        env: CLVMObjectType,
        max_cost: int,
        pre_eval_f: Optional[
            Callable[[CLVMObjectType, CLVMObjectType], Tuple[int, CLVMObjectType]]
        ] = None,
    ) -> Tuple[int, CLVMObjectType]:
        cost, r = _run_program(
            program,
            env,
            self.multi_op_fn,
            self.quote_kw,
            self.apply_kw,
            max_cost,
            pre_eval_f,
        )
        return cost, self.to_python(r)


def native_new_dialect(
    quote_kw: bytes, apply_kw: bytes, strict: bool, to_python: ConversionFn
) -> Dialect:
    unknown_op_callback = (
        clvm_rs.NATIVE_OP_UNKNOWN_STRICT
        if strict
        else clvm_rs.NATIVE_OP_UNKNOWN_NON_STRICT
    )
    dialect = clvm_rs.Dialect(
        quote_kw,
        apply_kw,
        unknown_op_callback,
        to_python=to_python,
    )
    return dialect


def python_new_dialect(
    quote_kw: bytes, apply_kw: bytes, strict: bool, to_python: ConversionFn
) -> Dialect:
    unknown_op_callback = (
        handle_unknown_op_strict if strict else handle_unknown_op_softfork_ready
    )
    dialect = Dialect(
        quote_kw,
        apply_kw,
        unknown_op_callback,
        to_python=to_python,
    )
    return dialect


def new_dialect(
    quote_kw: bytes,
    apply_kw: bytes,
    strict: bool,
    to_python: ConversionFn,
    backend=None,
):
    if backend is None:
        backend = "python" if clvm_rs is None else "native"
    backend_f = native_new_dialect if backend == "native" else python_new_dialect
    return backend_f(quote_kw, apply_kw, strict, to_python)
