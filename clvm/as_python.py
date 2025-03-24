from __future__ import annotations

from typing import Any, Callable, List, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from clvm.SExp import SExp

OpCallable = Callable[["OpStackType", "ValStackType"], None]

PythonReturnType = Union[
    bytes, Tuple["PythonReturnType", "PythonReturnType"], List["PythonReturnType"]
]

ValType = Union["SExp", PythonReturnType]
ValStackType = List[ValType]

OpStackType = List[OpCallable]


def _roll(op_stack: OpStackType, val_stack: ValStackType) -> None:
    v1 = val_stack.pop()
    v2 = val_stack.pop()
    val_stack.append(v1)
    val_stack.append(v2)


MakeTupleValStackType = List[
    Union[bytes, Tuple[object, object], "MakeTupleValStackType"]
]


def _make_tuple(op_stack: OpStackType, val_stack: ValStackType) -> None:
    left: PythonReturnType = val_stack.pop()  # type: ignore[assignment]
    right: PythonReturnType = val_stack.pop()  # type: ignore[assignment]
    if right == b"":
        val_stack.append([left])
    elif isinstance(right, list):
        v = [left] + right
        val_stack.append(v)
    else:
        val_stack.append((left, right))


def _as_python(op_stack: OpStackType, val_stack: ValStackType) -> None:
    t: SExp = val_stack.pop()  # type: ignore[assignment]
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
        # we know that t.atom is not None here because the pair is None
        val_stack.append(t.atom)  # type:ignore[arg-type]


def as_python(sexp: SExp) -> Any:
    op_stack: OpStackType = [_as_python]
    val_stack: ValStackType = [sexp]
    while op_stack:
        op_f = op_stack.pop()
        op_f(op_stack, val_stack)
    return val_stack[-1]
