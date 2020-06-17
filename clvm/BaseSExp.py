class BaseSExp:
    ATOM_TYPES = (bytes,)

    def __init__(self, v):
        assert (
            (v is None)
            or (isinstance(v, tuple) and len(v) == 2)
            or isinstance(v, self.ATOM_TYPES)
        )
        self.v = v

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

    def cons(self, right):
        return self.__class__((self, right))


BaseSExp.false = BaseSExp.__null__ = BaseSExp(b"")
BaseSExp.true = BaseSExp(b"\1")
