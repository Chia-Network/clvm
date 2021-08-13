from .SExp import SExp
from .casts import int_to_bytes
from .types import CLVMObjectType, ConversionFn, MultiOpFn, OperatorDict
from .chainable_multi_op_fn import ChainableMultiOpFn
from .handle_unknown_op import (
    handle_unknown_op_softfork_ready,
    handle_unknown_op_strict,
)
from .dialect import (
    ConversionFn,
    Dialect,
    new_dialect,
    opcode_table_for_backend,
    python_new_dialect,
    native_new_dialect,
)
from .chia_dialect_constants import KEYWORDS, KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM  # noqa
from .operators import OPERATOR_LOOKUP


def configure_chia_dialect(dialect: Dialect, backend=None) -> Dialect:
    quote_kw = KEYWORD_TO_ATOM["q"]
    apply_kw = KEYWORD_TO_ATOM["a"]
    table = opcode_table_for_backend(KEYWORD_TO_ATOM, backend=backend)
    dialect.update(table)
    return dialect


def chia_dialect(strict: bool, to_python: ConversionFn, backend=None) -> Dialect:
    dialect = new_dialect(quote_kw, apply_kw, strict, to_python, backend=backend)
    return configure_chia_dialect(dialect, backend)


class DebugDialect(Dialect):
    def __init__(
        self,
        quote_kw: bytes,
        apply_kw: bytes,
        multi_op_fn: MultiOpFn,
        to_python: ConversionFn,
    ):
        super().__init__(quote_kw, apply_kw, multi_op_fn, to_python)
        self.tracer = lambda x, y: None

    def do_sha256_with_trace(self, prev):
        def _run(value, max_cost=None):
            try:
                cost, result = prev(value)
            except TypeError:
                cost, result = prev(value, max_cost)

            self.tracer(value, result)
            return cost, result

        return _run

    def configure(self, **kwargs):
        if "sha256_tracer" in kwargs:
            self.tracer = kwargs["sha256_tracer"]


def chia_python_new_dialect(
    quote_kw: bytes,
    apply_kw: bytes,
    strict: bool,
    to_python: ConversionFn,
    backend="python",
) -> Dialect:
    unknown_op_callback = (
        handle_unknown_op_strict if strict else handle_unknown_op_softfork_ready
    )

    # Setup as a chia style clvm provider giving the chia operators.
    return configure_chia_dialect(
        DebugDialect(quote_kw, apply_kw, OPERATOR_LOOKUP, to_python), backend
    )


# Dialect that can allow acausal tracing of sha256 hashes.
def debug_new_dialect(
    quote_kw: bytes,
    apply_kw: bytes,
    strict: bool,
    to_python: ConversionFn,
    backend="python",
) -> Dialect:
    d = chia_python_new_dialect(quote_kw, apply_kw, strict, to_python, backend)

    # Override operators we want to track.
    std_op_table = opcode_table_for_backend(KEYWORD_TO_ATOM, backend="python")
    table = {b"\x0b": d.do_sha256_with_trace(std_op_table[b"\x0b"])}
    d.update(table)

    return d


dialect_factories = {
    "python": chia_python_new_dialect,
    "native": native_new_dialect,
    "debug": debug_new_dialect,
}
