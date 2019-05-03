import io

from clvm.casts import int_to_bytes, int_from_bytes
from clvm.serialize import make_sexp_from_stream, sexp_to_stream
from clvm.subclass_sexp import subclass_sexp

from .Var import Var


class mixin:
    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    def is_var(self):
        return isinstance(self.v, Var)

    def is_bytes(self):
        return isinstance(self.v, bytes)

    def var_index(self):
        if self.is_var():
            return self.v.index

    def as_bytes(self):
        if self.is_bytes():
            return self.as_atom()

    def type_index(self):
        # ATOM_TYPES = enum.IntEnum("ATOM_TYPES", "VAR BLOB PAIR")
        if self.is_var():
            return 0
        if self.is_bytes():
            return 1
        return 2

    def __len__(self):
        return len(list(self.as_iter()))

    def __iter__(self):
        return self.as_iter()

    def get_sublist_at_index(self, s):
        v = self
        while s > 0:
            v = v.v[1]
            s -= 1
        return v

    def get_at_index(self, s):
        return self.get_sublist_at_index(s).v[0]

    def __getitem__(self, s):
        if isinstance(s, int):
            return self.get_at_index(s)
        if s.stop is None and s.step is None:
            return self.get_sublist_at_index(s.start)

    @classmethod
    def from_stream(class_, f):
        return sexp_from_stream(f)

    @classmethod
    def from_blob(class_, blob):
        return class_.from_stream(io.BytesIO(blob))


to_sexp_f = subclass_sexp(mixin, (bytes, Var))

# HACK

SExp = to_sexp_f(None).__class__
SExp.false = to_sexp_f(0)
sexp_from_stream = make_sexp_from_stream(to_sexp_f)
