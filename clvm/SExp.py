import io
import typing

from blspy import G1Element

from .as_python import as_python
from .CLVMObject import CLVMObject

from .EvalError import EvalError

from .casts import (
    int_from_bytes,
    int_to_bytes,
)
from .serialize import sexp_to_stream


CastableType = typing.Union[
    "SExp",
    "CLVMObject",
    bytes,
    str,
    int,
    None,
    G1Element,
    list,
    typing.Tuple[typing.Any, typing.Any],
]


NULL = b""


def looks_like_clvm_object(o: typing.Any) -> bool:
    return hasattr(o, "atom") and hasattr(o, "pair")


# this function recognizes some common types and turns them into plain bytes,
def convert_atom_to_bytes(
    v: typing.Union[bytes, str, int, G1Element, None, list],
) -> bytes:

    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        return v.encode()
    if isinstance(v, int):
        return int_to_bytes(v)
    if isinstance(v, G1Element):
        return bytes(v)
    if v is None:
        return b""
    if v == []:
        return b""

    raise ValueError("can't cast %s (%s) to bytes" % (type(v), v))


def to_sexp_type(
    v: CastableType,
):

    if isinstance(v, (SExp, CLVMObject)):
        return v

    if isinstance(v, tuple):
        return CLVMObject((
            to_sexp_type(v[0]),
            to_sexp_type(v[1]),
        ))

    if isinstance(v, list):
        if len(v):
            return CLVMObject((
                to_sexp_type(v[0]),
                to_sexp_type(v[1:]),
            ))
        else:
            return CLVMObject(NULL)

    return CLVMObject(convert_atom_to_bytes(v))


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
    true: "SExp"
    false: "SExp"
    __null__: "SExp"

    # the underlying object implementing the clvm object protocol
    atom: typing.Optional[bytes]

    # this is a tuple of the otherlying CLVMObject-like objects. i.e. not
    # SExp objects with higher level functions, or None
    pair: typing.Optional[typing.Tuple[typing.Any, typing.Any]]

    def __init__(self, obj, _bin=None):
        self.atom = obj.atom
        self.pair = obj.pair

        self._bin = _bin

    # this returns a tuple of two SExp objects, or None
    def as_pair(self) -> typing.Tuple["SExp", "SExp"]:
        pair = self.pair
        if pair is None:
            return pair
        return (self.to(pair[0]), self.to(pair[1]))

    # TODO: deprecate this. Same as .atom property
    def as_atom(self):
        return self.atom

    def listp(self):
        return self.pair is not None

    def nullp(self):
        v = self.atom
        return v is not None and len(v) == 0

    def as_int(self):
        return int_from_bytes(self.atom)

    def as_bin(self):
        if self._bin is None:
            f = io.BytesIO()
            sexp_to_stream(self, f)
            self._bin = f.getvalue()

        return self._bin

    @classmethod
    def to(class_, v: CastableType) -> "SExp":
        if isinstance(v, class_):
            return v

        if looks_like_clvm_object(v):
            return class_(v)

        # this will lazily convert elements
        return class_(to_sexp_type(v))

    def cons(self, right):
        return self.to((self, right))

    def first(self):
        pair = self.pair
        if pair:
            return self.to(pair[0])
        raise EvalError("first of non-cons", self)

    def rest(self):
        pair = self.pair
        if pair:
            return self.to(pair[1])
        raise EvalError("rest of non-cons", self)

    @classmethod
    def null(class_):
        return class_.__null__

    def as_iter(self):
        v = self
        while not v.nullp():
            yield v.first()
            v = v.rest()

    def __eq__(self, other: CastableType):
        try:
            return self.as_bin() == self.to(other).as_bin()
        except ValueError:
            return False

    def list_len(self):
        v = self
        size = 0
        while v.listp():
            size += 1
            v = v.rest()
        return size

    def as_python(self):
        return as_python(self)

    def __str__(self):
        return self.as_bin().hex()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self))


SExp.false = SExp.__null__ = SExp(CLVMObject(b""))
SExp.true = SExp(CLVMObject(b"\1"))
