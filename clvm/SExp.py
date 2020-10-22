import io

from blspy import G1Element

try:
    from clvm_rust import PySExp as BaseSExp
except ImportError:
    from .BaseSExp import BaseSExp

from .EvalError import EvalError

from .casts import (
    int_from_bytes,
    int_to_bytes,
)
from .serialize import sexp_to_stream


class SExp(BaseSExp):
    ATOM_TYPES = (bytes,)

    @classmethod
    def to_castable(class_, v):
        return v

    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        if isinstance(v, G1Element):
            v = bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def as_bytes(self):
        return self.as_atom()

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    def as_pair(self):
        pair = super(SExp, self).as_pair()
        if pair is None:
            return pair
        return (SExp.to(pair[0]), SExp.to(pair[1]))

    @classmethod
    def to(class_, v):
        v = class_.to_castable(v)

        if isinstance(v, class_):
            return v

        if isinstance(v, BaseSExp):
            if v.listp():
                return class_(v.as_pair())
            return class_.to(v.as_atom())

        if v is None:
            return class_.null()

        if isinstance(v, tuple):
            assert len(v) == 2
            left = class_.to(v[0])
            right = class_.to(v[1])
            return class_((left, right))

        v = class_.to_atom(v)

        if isinstance(v, class_.ATOM_TYPES):
            return class_(v)

        if hasattr(v, "__iter__"):
            r = class_.null()
            for _ in reversed(v):
                r = class_.to(_).cons(r)
            return r

        raise ValueError("can't cast to %s: %s" % (class_, v))

    def first(self):
        pair = self.as_pair()
        if pair:
            return pair[0]
        raise EvalError("first of non-cons", self)

    def rest(self):
        pair = self.as_pair()
        if pair:
            return pair[1]
        raise EvalError("rest of non-cons", self)

    def cons(self, right):
        return self.__class__((self, right))

    @classmethod
    def null(class_):
        return class_.__null__

    def as_iter(self):
        v = self
        while not v.nullp():
            yield v.first()
            v = v.rest()

    def __eq__(self, other):
        try:
            other = self.to(other)
        except ValueError:
            return False
        if self.listp():
            if other.listp():
                return self.as_pair() == other.as_pair()
            else:
                return False
        return self.as_atom() == other.as_atom()

    def as_python(self):
        if self.listp():
            f, r = self.as_pair()
            if r.nullp():
                return [f.as_python()]
            if r.listp():
                partial_list = [f.as_python()]
                partial_list.extend(r.as_python())
                return partial_list
            return (f.as_python(), r.as_python())
        return self.as_atom()

    def __str__(self):
        return str(self.as_python())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self))


SExp.false = SExp.__null__ = SExp(b"")
SExp.true = SExp.to(b"\1")
