import io

from .CoreSExp import CoreSExp
from .EvalError import EvalError

from .casts import (
    int_from_bytes,
    int_to_bytes,
    bls12_381_from_bytes,
    bls12_381_to_bytes,
    bls12_381_generator,
)
from .serialize import sexp_to_stream


class SExp(CoreSExp):
    @classmethod
    def to_castable(class_, v):
        return v

    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        if isinstance(v, bls12_381_generator.__class__):
            v = bls12_381_to_bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def as_bytes(self):
        return self.as_atom()

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    def as_bls12_381(self):
        return bls12_381_from_bytes(self.as_atom())

    @classmethod
    def to(class_, v):
        v = class_.to_castable(v)

        if isinstance(v, class_):
            return v

        if isinstance(v, CoreSExp):
            if v.listp():
                return class_.to(v.as_pair())
            return class_.to(v.as_atom())

        if v is None:
            return class_.null()

        if isinstance(v, tuple):
            assert len(v) == 2
            return class_((class_.to(v[0]), class_.to(v[1])))

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

    @classmethod
    def null(class_):
        return class_.__null__

    def is_legit_list(self):
        # return False if it's a cons box that doesn't have a null
        if self.nullp():
            return True
        if self.listp():
            return self.rest().is_legit_list()
        return False

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
        if self.listp() != other.listp():
            return False
        if self.listp():
            pair = self.as_pair()
            if other.listp():
                other_pair = other.as_pair()
                return pair[0] == other_pair[0] and pair[1] == other_pair[1]
            return False
        return self.as_atom() == other.as_atom()

    def as_python(self):
        if not self.listp():
            return self.as_atom()

        left, right = self.as_pair()
        r = [left.as_python()]
        while right.listp():
            left, right = right.as_pair()
            r.append(left.as_python())
            if right.nullp():
                return r
        r[-1] = (r[-1], right.as_python())
        return r

    def __str__(self):
        return str(self.as_python())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self))


SExp.false = SExp.__null__ = SExp.to(b"")
SExp.true = SExp.to(b"\1")


def subclass_sexp(*args, **kwargs):
    return SExp.to
