from __future__ import annotations

import io
import typing

import typing_extensions

from .as_python import as_python
from .CLVMObject import CLVMObject, CLVMStorage

from .EvalError import EvalError

from .casts import (
    int_from_bytes,
    int_to_bytes,
)
from .serialize import sexp_to_stream


CastableType = typing.Union[
    "SExp",
    CLVMStorage,
    typing.SupportsBytes,
    bytes,
    str,
    int,
    None,
    typing.Sequence["CastableType"],
    typing.Tuple["CastableType", "CastableType"],
]


NULL = b""


def looks_like_clvm_object(o: typing.Any) -> typing_extensions.TypeGuard[CLVMStorage]:
    d = dir(o)
    return "atom" in d and "pair" in d


# this function recognizes some common types and turns them into plain bytes,
def convert_atom_to_bytes(
    v: typing.Union[
        bytes,
        str,
        int,
        None,
        typing.List[typing_extensions.Never],
        typing.SupportsBytes,
    ],
) -> bytes:
    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        return v.encode()
    if isinstance(v, int):
        return int_to_bytes(v)
    if v is None:
        return b""
    if v == []:
        return b""
    if hasattr(v, "__bytes__"):
        return bytes(v)

    raise ValueError("can't cast %s (%s) to bytes" % (type(v), v))


ValType = typing.Union["SExp", CastableType]
StackType = typing.List[ValType]


# returns a clvm-object like object
@typing.no_type_check
def to_sexp_type(
    v: CastableType,
) -> CLVMStorage:
    stack = [v]
    ops = [(0, None)]  # convert

    while len(ops) > 0:
        op, target = ops.pop()
        # convert value
        if op == 0:
            if looks_like_clvm_object(stack[-1]):
                continue
            v = stack.pop()
            if isinstance(v, tuple):
                if len(v) != 2:
                    raise ValueError("can't cast tuple of size %d" % len(v))
                left, right = v
                target = len(stack)
                stack.append(CLVMObject((left, right)))
                if not looks_like_clvm_object(right):
                    stack.append(right)
                    ops.append((2, target))  # set right
                    ops.append((0, None))  # convert
                if not looks_like_clvm_object(left):
                    stack.append(left)
                    ops.append((1, target))  # set left
                    ops.append((0, None))  # convert
                continue
            if isinstance(v, list):
                target = len(stack)
                stack.append(CLVMObject(NULL))
                for _ in v:
                    stack.append(_)
                    ops.append((3, target))  # prepend list
                    # we only need to convert if it's not already the right
                    # type
                    if not looks_like_clvm_object(_):
                        ops.append((0, None))  # convert
                continue
            stack.append(CLVMObject(convert_atom_to_bytes(v)))
            continue

        if op == 1:  # set left
            stack[target].pair = (CLVMObject(stack.pop()), stack[target].pair[1])
            continue
        if op == 2:  # set right
            stack[target].pair = (stack[target].pair[0], CLVMObject(stack.pop()))
            continue
        if op == 3:  # prepend list
            stack[target] = CLVMObject((stack.pop(), stack[target]))
            continue
    # there's exactly one item left at this point
    if len(stack) != 1:
        raise ValueError("internal error")

    # stack[0] implements the clvm object protocol and can be wrapped by an SExp
    return stack[0]


_T_SExp = typing.TypeVar("_T_SExp", bound="SExp")


class SExp:
    """
    SExp provides higher level API on top of any object implementing the CLVM
    object protocol.
    The tree of values is not a tree of SExp objects, it's a tree of CLVMObject
    like objects. SExp simply wraps them to privide a uniform view of any
    underlying conforming tree structure.

    The CLVM object protocol (concept) exposes two attributes:
    1. "atom" which is either None or bytes
    2. "pair" which is either None or a tuple of exactly two elements. Both
       elements implementing the CLVM object protocol.
    Exactly one of "atom" and "pair" must be None.
    """

    true: typing.ClassVar[SExp]
    false: typing.ClassVar[SExp]
    __null__: typing.ClassVar[SExp]

    # the underlying object implementing the clvm object protocol
    atom: typing.Optional[bytes]

    # this is a tuple of the otherlying CLVMObject-like objects. i.e. not
    # SExp objects with higher level functions, or None
    pair: typing.Optional[typing.Tuple[CLVMStorage, CLVMStorage]]

    def __init__(self, obj: CLVMStorage) -> None:
        self.atom = obj.atom
        self.pair = obj.pair

    # this returns a tuple of two SExp objects, or None
    def as_pair(self) -> typing.Optional[typing.Tuple[SExp, SExp]]:
        pair = self.pair
        if pair is None:
            return pair
        return (self.__class__(pair[0]), self.__class__(pair[1]))

    # TODO: deprecate this. Same as .atom property
    def as_atom(self) -> typing.Optional[bytes]:
        return self.atom

    def listp(self) -> bool:
        return self.pair is not None

    def nullp(self) -> bool:
        v = self.atom
        return v is not None and len(v) == 0

    def as_int(self) -> int:
        if self.atom is None:
            raise TypeError("Unable to convert a pair to an int")
        return int_from_bytes(self.atom)

    def as_bin(self, *, allow_backrefs: bool = False) -> bytes:
        f = io.BytesIO()
        sexp_to_stream(self, f, allow_backrefs=allow_backrefs)
        return f.getvalue()

    # TODO: should be `v: CastableType`
    @classmethod
    def to(cls: typing.Type[_T_SExp], v: typing.Any) -> _T_SExp:
        if isinstance(v, cls):
            return v

        if looks_like_clvm_object(v):
            return cls(v)

        # this will lazily convert elements
        return cls(to_sexp_type(v))

    def cons(self: _T_SExp, right: _T_SExp) -> _T_SExp:
        return self.to((self, right))

    def first(self: _T_SExp) -> _T_SExp:
        pair = self.pair
        if pair:
            return self.__class__(pair[0])
        raise EvalError("first of non-cons", self)

    def rest(self: _T_SExp) -> _T_SExp:
        pair = self.pair
        if pair:
            return self.__class__(pair[1])
        raise EvalError("rest of non-cons", self)

    @classmethod
    def null(class_) -> SExp:
        return class_.__null__

    def as_iter(self: _T_SExp) -> typing.Iterator[_T_SExp]:
        v = self
        while v.pair is not None:
            yield v.first()
            v = v.rest()

    def __eq__(self, other: object) -> bool:
        try:
            other = self.to(typing.cast(CastableType, other))
            to_compare_stack = [(self, other)]
            while to_compare_stack:
                s1, s2 = to_compare_stack.pop()
                p1 = s1.as_pair()
                if p1:
                    p2 = s2.as_pair()
                    if p2:
                        to_compare_stack.append((p1[0], p2[0]))
                        to_compare_stack.append((p1[1], p2[1]))
                    else:
                        return False
                elif s2.as_pair() or s1.as_atom() != s2.as_atom():
                    return False
            return True
        except ValueError:
            return False

    def list_len(self) -> int:
        v = self
        size = 0
        while v.listp():
            size += 1
            v = v.rest()
        return size

    def as_python(self) -> typing.Any:
        return as_python(self)

    def __str__(self) -> str:
        return self.as_bin().hex()

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, str(self))


SExp.false = SExp.__null__ = SExp(CLVMObject(b""))
SExp.true = SExp(CLVMObject(b"\1"))
