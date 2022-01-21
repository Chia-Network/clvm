from dataclasses import dataclass
from typing import Optional, Tuple

from .types import CLVMObjectType, MultiOpFn, OperatorDict


@dataclass
class ChainableMultiOpFn:
    """
    This structure handles clvm operators. Given an atom, it looks it up in a `dict`, then
    falls back to calling `unknown_op_handler`.
    """

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
