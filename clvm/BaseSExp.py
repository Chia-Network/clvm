"""
This is the minimal `SExp` type that defines how and where its contents are
stored in the heap. The methods here are the only ones required for `run_program`.
A native implementation of `run_program` should implement this base class.
"""


class BaseSExp:
    ATOM_TYPES = (bytes,)

    def __new__(class_, v):
        assert (
            (v is None)
            or (isinstance(v, tuple) and len(v) == 2)
            or isinstance(v, class_.ATOM_TYPES)
        )
        self = super(BaseSExp, class_).__new__(class_)
        self.v = v
        return self

    def listp(self):
        return isinstance(self.v, (None.__class__, tuple))

    def nullp(self):
        return self == self.__null__

    def as_pair(self):
        if self.listp():
            return self.v
        return None

    def as_atom(self):
        assert not (self.listp())
        if self.listp():
            return None
        return self.v


BaseSExp.false = BaseSExp.__null__ = BaseSExp(b"")
BaseSExp.true = BaseSExp(b"\1")
