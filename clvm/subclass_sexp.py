from .EvalError import EvalError


class BaseSExp:
    ATOM_TYPES = (bytes, )

    @classmethod
    def to_castable(class_, v):
        return v

    @classmethod
    def to_atom(class_, v):
        return v

    @classmethod
    def to(class_, v):
        v = class_.to_castable(v)

        if isinstance(v, class_):
            return v

        if isinstance(v, BaseSExp):
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

        raise ValueError("can't cast to %s: %s" % (class_, v))

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
        return self == self.__null__

    def cons(self, right):
        return self.__class__((self, right))

    def first(self):
        if isinstance(self.v, tuple):
            return self.v[0]
        raise EvalError("first of non-cons", self)

    def rest(self):
        if isinstance(self.v, tuple):
            return self.v[1]
        raise EvalError("rest of non-cons", self)

    def as_atom(self):
        assert not(self.listp())
        return self.v

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
        assert self.is_legit_list()
        if self.nullp():
            return
        yield self.first()
        yield from self.rest().as_iter()

    def __eq__(self, other):
        try:
            other = self.to(other)
        except ValueError:
            return False
        return other.v == self.v

    def as_python(self):
        if isinstance(self.v, self.ATOM_TYPES):
            return self.v
        if self.is_legit_list():
            return list(_.as_python()for _ in self.as_iter())
        return tuple((self.first().as_python(), self.rest().as_python()))

    def __str__(self):
        return str(self.as_python())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self))


def subclass_sexp(mixin_class=object, atom_types=BaseSExp.ATOM_TYPES, true=b'\1', false=None):

    class SExp(mixin_class, BaseSExp):
        ATOM_TYPES = atom_types

    SExp.__null__ = SExp(false)
    SExp.false = SExp.__null__
    SExp.true = SExp(true)

    return SExp.to
