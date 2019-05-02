from .ReduceError import ReduceError


class RExp:
    ATOM_TYPES = (bytes, )

    @classmethod
    def to_atom(class_, v):
        return v

    @classmethod
    def to(class_, v):
        if isinstance(v, class_):
            return v

        if isinstance(v, RExp):
            return class_.to(v.v)

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

        raise ValueError("bad atom %s" % v)

    def __init__(self, v):
        assert (
            (v is None) or
            (isinstance(v, tuple) and len(v) == 2) or
            isinstance(v, self.ATOM_TYPES)
        )
        self.v = v

    def listp(self):
        return isinstance(self.v, (None.__class__, tuple))

    def nullp(self):
        return self.v is None

    def cons(self, right):
        return self.__class__((self, right))

    def first(self):
        if isinstance(self.v, tuple):
            return self.v[0]
        raise ReduceError("first of non-cons")

    def rest(self):
        if isinstance(self.v, tuple):
            return self.v[1]
        raise ReduceError("rest of non-cons")

    def as_atom(self):
        assert not(self.listp())
        return self.v

    def as_obj(self):
        if self.listp():
            return [_.as_obj() for _ in self.as_iter()]
        return self.v

    @classmethod
    def null(class_):
        return class_.__null__

    def as_iter(self):
        if self.nullp():
            return
        assert self.listp()
        yield self.first()
        yield from self.rest().as_iter()

    def __repr__(self):
        t = "??"
        if self.nullp():
            t = None
        elif self.listp():
            t = repr([_.as_obj() for _ in self.as_iter()])
        else:
            t = repr(self.v)
        return "%s(%s)" % (self.__class__.__name__, t)

    def __eq__(self, other):
        try:
            other = self.to(other)
        except ValueError:
            return False
        return other.v == self.v


def subclass_rexp(mixin_class=object, atom_types=RExp.ATOM_TYPES):

    class SExp(mixin_class, RExp):
        ATOM_TYPES = atom_types

    SExp.__null__ = SExp(None)
    SExp.false = SExp.__null__
    SExp.true = SExp(b'\1')

    return SExp.to
