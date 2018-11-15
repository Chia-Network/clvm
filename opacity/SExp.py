import enum
import io

from dataclasses import dataclass

from .casts import int_to_bytes, int_from_bytes
from .serialize import sexp_from_stream, sexp_to_stream


@dataclass
class Var:
    index: int

    def __repr__(self):
        return "x%d" % self.index


ATOM_TYPES = enum.IntEnum("ATOM_TYPES", "VAR BLOB LIST")


class SExp:
    item: object
    type: ATOM_TYPES

    def __init__(self, v):

        if isinstance(v, SExp):
            self.item = v.item
            self.type = v.type
            return

        def to_sexp(v):
            if isinstance(v, SExp):
                return v
            return SExp(v)

        if isinstance(v, int):
            v = int_to_bytes(v)

        if isinstance(v, bytes):
            self.item = v
            self.type = ATOM_TYPES.BLOB
        elif isinstance(v, Var):
            self.item = v.index
            self.type = ATOM_TYPES.VAR
        elif isinstance(v, tuple):
            assert len(v) == 2
            assert isinstance(v[0], SExp)
            self.item = v
            self.type = ATOM_TYPES.LIST
        elif hasattr(v, "__iter__"):
            rest = None
            for _ in reversed(v):
                rest = (to_sexp(_), rest)
            self.item = rest
            self.type = ATOM_TYPES.LIST
        else:
            raise ValueError("bad type for %s" % v)

    @classmethod
    def from_stream(class_, f):
        return sexp_from_stream(f, class_)

    @classmethod
    def from_blob(class_, blob):
        return class_.from_stream(io.BytesIO(blob))

    @classmethod
    def from_var_index(class_, index):
        return class_(Var(index))

    def is_var(self):
        return self.type == ATOM_TYPES.VAR

    def is_bytes(self):
        return self.type == ATOM_TYPES.BLOB

    def is_list(self):
        return self.type == ATOM_TYPES.LIST

    def var_index(self):
        if self.is_var():
            return self.item

    def as_int(self):
        if self.is_bytes():
            return int_from_bytes(self.as_bytes())

    def as_bytes(self):
        if self.is_bytes():
            return self.item

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    def __iter__(self):
        v = self.item
        while True:
            if v is None:
                break
            yield v[0]
            v = v[1]

    def __len__(self):
        return sum(1 for _ in self)

    def get_sublist_at_index(self, s):
        v = self.item
        while s > 0:
            v = v[1]
            s -= 1
        return SExp(v)

    def get_at_index(self, s):
        return self.get_sublist_at_index(s).item[0]

    def __getitem__(self, s):
        if isinstance(s, int):
            return self.get_at_index(s)
        if s.stop == s.step == None:
            return self.get_sublist_at_index(s.start)

    def as_obj(self):
        type = self.type
        if type == ATOM_TYPES.VAR:
            return Var(index=self.var_index())
        if type == ATOM_TYPES.BLOB:
            return self.item
        if type == ATOM_TYPES.LIST:
            return [_.as_obj() for _ in self]
        assert 0

    def __repr__(self):
        t = "??"
        if self.is_var():
            t = "x%d" % self.item
        if self.is_bytes():
            t = repr(self.item)
        if self.is_list():
            t = repr([_.as_obj() for _ in self])
        return "SExp(%s)" % t

    def __eq__(self, other):
        try:
            other = SExp(other)
        except ValueError:
            return False
        return other.type == self.type and other.item == self.item
