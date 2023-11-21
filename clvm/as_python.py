from __future__ import annotations

from typing import Any, Callable, List, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from clvm.SExp import SExp

OpCallable = Callable[["OpStackType", "ValStackType"], None]

ValType = Union[SExp, List["ValType"], Tuple["ValType", ...]]
ValStackType = List[Union[ValType, "ValStackType"]]
OpStackType = List[OpCallable]

# TODO: hum...
PythonType = Union[int, bytes, str, List["PythonType"], Tuple["PythonType", "PythonType"]]


def _roll(op_stack: OpStackType, val_stack: List[object]) -> None:
    v1 = val_stack.pop()
    v2 = val_stack.pop()
    val_stack.append(v1)
    val_stack.append(v2)


# MakeTupleValType = Union[bytes,
MakeTupleValStackType = List[Union[bytes, Tuple[object, object], "MakeTupleValStackType"]]


def _make_tuple(op_stack: OpStackType, val_stack: MakeTupleValStackType) -> None:
    left = val_stack.pop()
    right = val_stack.pop()
    if right == b"":
        val_stack.append([left])
    elif isinstance(right, list):
        v = [left] + right
        val_stack.append(v)
    else:
        val_stack.append((left, right))


def _as_python(op_stack: OpStackType, val_stack: List[SExp]) -> None:
    t = val_stack.pop()
    pair = t.as_pair()
    if pair:
        left, right = pair
        op_stack.append(_make_tuple)
        op_stack.append(_as_python)
        op_stack.append(_roll)
        op_stack.append(_as_python)
        val_stack.append(left)
        val_stack.append(right)
    else:
        # TODO: do we have to ignore?
        val_stack.append(t.atom)  # type:ignore[arg-type]


# TODO: probably have to just accept this Any, but...
def as_python(sexp: SExp) -> Any:
    op_stack: OpStackType = [_as_python]
    val_stack: List[SExp] = [sexp]
    while op_stack:
        op_f = op_stack.pop()
        op_f(op_stack, val_stack)
    return val_stack[-1]
