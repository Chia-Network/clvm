from dataclasses import dataclass

from typing import Any, Callable, Dict, Optional, Tuple, Union

from .run_program import _run_program

CLVMAtom = Any
CLVMPair = Any

CLVMObjectType = Union["CLVMAtom", "CLVMPair"]


MultiOpFn = Callable[[bytes, CLVMObjectType, int], Tuple[int, CLVMObjectType]]

OpFn = Callable[[CLVMObjectType, int], Tuple[int, CLVMObjectType]]

OperatorDict = Dict[bytes, Callable[[CLVMObjectType, int], Tuple[int, CLVMObjectType]]]


@dataclass
class ChainableMultiOpFn:
    op_lookup: OperatorDict
    unknown_op_handler: MultiOpFn

    def __call__(
        self, op: bytes, arguments: CLVMObjectType, max_cost: Optional[int] = None
    ) -> Tuple[int, CLVMObjectType]:
        f = self.op_lookup.get(op)
        if f:
            try:
                return f(arguments)
            except TypeError:
                # some operators require `max_cost`
                return f(arguments, max_cost)
        return self.unknown_op_handler(op, arguments, max_cost)


@dataclass
class DialectInfo:
    quote_kw: bytes
    apply_kw: bytes
    opcode_lookup: OperatorDict


class Dialect:
    def __init__(
        self,
        quote_kw: bytes,
        apply_kw: bytes,
        multi_op_fn: MultiOpFn,
    ):
        self.quote_kw = quote_kw
        self.apply_kw = apply_kw
        self.multi_op_fn = multi_op_fn

    def run_program(
        self,
        program: CLVMObjectType,
        env: CLVMObjectType,
        max_cost: int,
        pre_eval_f: Optional[
            Callable[[CLVMObjectType, CLVMObjectType], Tuple[int, CLVMObjectType]]
        ] = None,
    ) -> Tuple[int, CLVMObjectType]:
        return _run_program(
            program,
            env,
            self.multi_op_fn,
            self.quote_kw,
            self.apply_kw,
            max_cost,
            pre_eval_f,
        )
