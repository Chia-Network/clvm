import io
import typing

from blspy import G1Element

from .as_python import as_python
from .BaseSExp import BaseSExp, SExpType

from .EvalError import EvalError

from .casts import (
    int_from_bytes,
    int_to_bytes,
)
from .serialize import sexp_to_stream


CastableType = typing.Union[
    "SExp",
    BaseSExp,
    bytes,
    int,
    None,
    SExpType,
    G1Element,
    typing.Tuple[typing.Any, typing.Any],
]

NULL = b""


class SExp(BaseSExp):
    true: "SExp"
    false: "SExp"
    __null__: "SExp"

    @classmethod
    def _to_sexp_type(
        class_,
        v: CastableType,
    ) -> SExpType:
        if isinstance(v, tuple):
            assert len(v) == 2
            left, right = v
            if type(left) != BaseSExp:
                left = BaseSExp(class_._to_sexp_type(left))
            if type(right) != BaseSExp:
                right = BaseSExp(class_._to_sexp_type(right))
            return (left, right)
        if isinstance(v, BaseSExp):
            return v.pair or v.atom
        if isinstance(v, bytes):
            return v

        if isinstance(v, int):
            return int_to_bytes(v)
        if isinstance(v, G1Element):
            return bytes(v)
        if v is None:
            return NULL
        if v == []:
            return NULL

        if hasattr(v, "__iter__"):
            pair: SExpType = NULL
            for _ in reversed(v):
                pair = (
                    class_.to(_),
                    class_.to(pair),
                )
            return pair

        raise ValueError("can't cast to %s: %s" % (class_, v))

    def as_pair(self):
        pair = self.pair
        if pair is None:
            return pair
        return (self.to(pair[0]), self.to(pair[1]))

    def as_atom(self):
        return self.atom

    def listp(self):
        return self.pair is not None

    def nullp(self):
        return self.atom == b""

    def as_int(self):
        return int_from_bytes(self.atom)

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    def validate(self):
        pair = self.pair
        if pair:
            assert len(pair) == 2
            pair[0].validate()
            pair[1].validate()
        else:
            assert isinstance(self.atom, bytes)

    @classmethod
    def to(class_, v: CastableType):
        if isinstance(v, class_):
            return v
        v1 = class_._to_sexp_type(v)
        return class_(v1)

    def cons(self, right: "BaseSExp"):
        s = super(SExp, self).cons(SExp.to(right))
        return self.to(s)

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
            other = self.to(other)
        except ValueError:
            return False
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

    def as_python(self):
        return as_python(self)

    def __str__(self):
        return self.as_bin().hex()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self))


SExp.false = SExp.__null__ = SExp(b"")
SExp.true = SExp(b"\1")
