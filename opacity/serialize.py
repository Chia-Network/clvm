import enum
import io

from dataclasses import dataclass


from .keywords import KEYWORD_FROM_INT


@dataclass
class Var:
    index: int


def int_from_bytes(blob):
    size = len(blob)
    if size == 0 or size > 16:
        return 0
    return int.from_bytes(blob, "big", signed=True)


def int_to_bytes(v):
    byte_count = (v.bit_length() + 8) >> 3
    if byte_count > 16:
        raise ValueError("int too large: %d" % v)
    if v == 0:
        return b''
    return v.to_bytes(byte_count, "big", signed=True)


ATOM_TYPES = enum.IntEnum("ATOM_TYPES", "VAR BLOB LIST KEYWORD")


def sexp_from_var(index):
    return SExp(index, ATOM_TYPES.VAR)


def sexp_from_list(iter):
    return SExp(list(iter), ATOM_TYPES.LIST)


def sexp_from_bytes(blob):
    return SExp(blob, ATOM_TYPES.BLOB)


def sexp_from_int(v):
    return sexp_from_bytes(int_to_bytes(v))


def sexp_from_keyword(v):
    return sexp_from_int(v)


@dataclass
class SExp:
    item: object
    type: ATOM_TYPES

    def is_var(self):
        return self.type == ATOM_TYPES.VAR

    def is_bytes(self):
        return self.type == ATOM_TYPES.BLOB

    def is_list(self):
        return self.type == ATOM_TYPES.LIST

    def is_keyword(self):
        return self.is_bytes()

    def var_index(self):
        if self.is_var():
            return self.item

    def as_keyword_index(self):
        return self.as_int()

    def as_int(self):
        if self.is_bytes():
            return int_from_bytes(self.as_bytes())

    def as_bytes(self):
        if self.is_bytes():
            return self.item

    def as_list(self):
        if self.is_list():
            return self.item

    def __repr__(self):
        if self.is_var():
            return "x%d" % self.item
        if self.is_bytes():
            return repr(self.item)
        if self.is_list():
            return repr(self.item)
        if self.is_keyword():
            _ = self.as_keyword_index()
            if _ < len(KEYWORD_FROM_INT):
                return KEYWORD_FROM_INT[_]
        return "??"

    def __eq__(self, other):
        other = to_sexp(other)
        return other.type == self.type and other.item == self.item


def to_sexp(v, is_first=False):
    if isinstance(v, SExp):
        return v

    if isinstance(v, (list, tuple)):
        return sexp_from_list([to_sexp(_, idx == 0) for idx, _ in enumerate(v)])

    if isinstance(v, int):
        return sexp_from_int(v)

    if isinstance(v, bytes):
        return sexp_from_bytes(v)

    if isinstance(v, str):
        return sexp_from_bytes(v.encode("utf8"))

    if isinstance(v, Var):
        return sexp_from_var(v.index)

    assert 0


def from_sexp(v):
    if not isinstance(v, SExp):
        return v

    if v.is_list():
        return [from_sexp(_) for _ in v.as_list()]

    if v.is_var():
        return Var(v.var_index())

    if v.is_bytes():
        return v.as_bytes()

    if v.is_keyword():
        return v.as_int()


def msgpack_types_to_cs_types(t):
    if isinstance(t, list):
        return sexp_from_list([msgpack_types_to_cs_types(_) for _ in t])

    if isinstance(t, int):
        if t >= 0:
            return sexp_from_keyword(t)
        else:
            return sexp_from_var(-t-1)

    return sexp_from_bytes(t)


def cs_types_to_msgpack_types(t):
    if t.is_list():
        return [cs_types_to_msgpack_types(_) for _ in t.as_list()]

    if t.is_bytes():
        return t.as_bytes()

    if t.is_var():
        return - t.var_index() - 1

    if t.is_keyword():
        return t.as_keyword_index()

    assert 0


def encode_size(f, size, step_size, base_byte_int):
    step_count, remainder = divmod(size, step_size)
    if step_count > 0:
        f.write(b'\x60')
        step_count -= 1
        while step_count > 0:
            step_count, r = divmod(step_count, 32)
            f.write(bytes([r]))
    f.write(bytes([base_byte_int+remainder]))


def to_stream(v, f):
    if v.is_bytes():
        blob = v.as_bytes()
        size = len(blob)
        if size == 0:
            f.write(b'\0')
            return
        if size == 1:
            v1 = v.as_int()
            if v1 and 0 < v1 <= 31:
                f.write(bytes([v1 & 0x3f]))
                return
        encode_size(f, size, 160, 0x60)
        f.write(blob)
        return

    if v.is_list():
        items = v.as_list()
        encode_size(f, len(items), 32, 0x20)
        for _ in items:
            to_stream(_, f)
        return

    if v.is_var():
        encode_size(f, v.var_index(), 32, 0x40)
        return

    assert 0


def decode_size(f):
    steps = 0
    v = f.read(1)[0]
    if v == 0x60:
        steps = 1
        shift_count = 0
        while True:
            v = f.read(1)[0]
            if v >= 0x20:
                break
            steps += (v << shift_count)
            shift_count += 5

    return steps, v


def from_stream(f):
    steps, v = decode_size(f)
    if v == 0:
        return sexp_from_bytes(b'')

    if v < 0x20:
        return sexp_from_bytes(bytes([v]))

    if v < 0x40:
        size = v - 0x20 + steps * 0x20
        items = [from_stream(f) for _ in range(size)]
        return sexp_from_list(items)

    if v < 0x60:
        index = v - 0x40 + steps * 0x20
        return sexp_from_var(index)

    size = v - 0x60 + steps * 160
    blob = f.read(size)
    return sexp_from_bytes(blob)


def unwrap_blob(blob):
    return from_stream(io.BytesIO(blob))


def wrap_blobs(blob_list):
    f = io.BytesIO()
    to_stream(to_sexp(blob_list), f)
    return f.getvalue()


def serialize_sexp(sexp):
    return wrap_blobs(sexp)


def deserialize_sexp(f):
    return from_stream(f)
