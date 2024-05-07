# decoding:
# read a byte
# if it's 0x80, it's nil (which might be same as 0)
# if it's 0xff, it's a cons box. Read two items, build cons
# otherwise, number of leading set bits is length in bytes to read size
# For example, if the bit fields of the first byte read are:
#   10xx xxxx -> 1 byte is allocated for size_byte, and the value of the size is 00xx xxxx
#   110x xxxx -> 2 bytes are allocated for size_byte, and the value of the size 000x xxxx xxxx xxxx
#   1110 xxxx -> 3 bytes allocated. The size is 0000 xxxx xxxx xxxx xxxx xxxx
#   1111 0xxx -> 4 bytes allocated.
#   1111 10xx -> 5 bytes allocated.
# If the first byte read is one of the following:
#   1000 0000 -> 0 bytes : nil
#   0000 0000 -> 1 byte : zero (b'\x00')
from __future__ import annotations

import io
import typing

from .CLVMObject import CLVMObject, CLVMStorage


if typing.TYPE_CHECKING:
    from .SExp import CastableType, SExp


MAX_SINGLE_BYTE = 0x7F
CONS_BOX_MARKER = 0xFF


T = typing.TypeVar("T")

ToCLVMStorage = typing.Callable[
    [typing.Union[bytes, typing.Tuple[CLVMStorage, CLVMStorage]]], CLVMStorage
]

OpCallable = typing.Callable[
    ["OpStackType", "ValStackType", typing.BinaryIO, ToCLVMStorage], None
]

ValStackType = typing.List[CLVMStorage]
OpStackType = typing.List[OpCallable]


def sexp_to_byte_iterator(sexp: CLVMStorage) -> typing.Iterator[bytes]:
    todo_stack = [sexp]
    while todo_stack:
        sexp = todo_stack.pop()
        pair = sexp.pair
        if pair:
            yield bytes([CONS_BOX_MARKER])
            todo_stack.append(pair[1])
            todo_stack.append(pair[0])
        else:
            assert sexp.atom is not None
            yield from atom_to_byte_iterator(sexp.atom)


def atom_to_byte_iterator(as_atom: bytes) -> typing.Iterator[bytes]:
    size = len(as_atom)
    if size == 0:
        yield b"\x80"
        return
    if size == 1:
        if as_atom[0] <= MAX_SINGLE_BYTE:
            yield as_atom
            return
    if size < 0x40:
        size_blob = bytes([0x80 | size])
    elif size < 0x2000:
        size_blob = bytes([0xC0 | (size >> 8), (size >> 0) & 0xFF])
    elif size < 0x100000:
        size_blob = bytes([0xE0 | (size >> 16), (size >> 8) & 0xFF, (size >> 0) & 0xFF])
    elif size < 0x8000000:
        size_blob = bytes(
            [
                0xF0 | (size >> 24),
                (size >> 16) & 0xFF,
                (size >> 8) & 0xFF,
                (size >> 0) & 0xFF,
            ]
        )
    elif size < 0x400000000:
        size_blob = bytes(
            [
                0xF8 | (size >> 32),
                (size >> 24) & 0xFF,
                (size >> 16) & 0xFF,
                (size >> 8) & 0xFF,
                (size >> 0) & 0xFF,
            ]
        )
    else:
        raise ValueError(f"sexp too long {as_atom!r}")

    yield size_blob
    yield as_atom


def sexp_to_stream(sexp: SExp, f: typing.BinaryIO) -> None:
    for b in sexp_to_byte_iterator(sexp):
        f.write(b)


def _op_read_sexp(
    op_stack: OpStackType,
    val_stack: ValStackType,
    f: typing.BinaryIO,
    to_sexp: ToCLVMStorage,
) -> None:
    blob = f.read(1)
    if len(blob) == 0:
        raise ValueError("bad encoding")
    b = blob[0]
    if b == CONS_BOX_MARKER:
        op_stack.append(_op_cons)
        op_stack.append(_op_read_sexp)
        op_stack.append(_op_read_sexp)
        return
    val_stack.append(_atom_from_stream(f, b, to_sexp))


def _op_cons(
    op_stack: OpStackType,
    val_stack: ValStackType,
    f: typing.BinaryIO,
    to_sexp: ToCLVMStorage,
) -> None:
    right = val_stack.pop()
    left = val_stack.pop()
    val_stack.append(to_sexp((left, right)))


def sexp_from_stream(f: typing.BinaryIO, to_sexp: typing.Callable[["CastableType"], T]) -> T:
    op_stack: OpStackType = [_op_read_sexp]
    val_stack: ValStackType = []

    while op_stack:
        func = op_stack.pop()
        func(op_stack, val_stack, f, CLVMObject)
    return to_sexp(val_stack.pop())


def _op_consume_sexp(f: typing.BinaryIO) -> typing.Tuple[bytes, int]:
    blob = f.read(1)
    if len(blob) == 0:
        raise ValueError("bad encoding")
    b = blob[0]
    if b == CONS_BOX_MARKER:
        return (blob, 2)
    return (_consume_atom(f, b), 0)


def _consume_atom(f: typing.BinaryIO, b: int) -> bytes:
    if b == 0x80:
        return bytes([b])
    if b <= MAX_SINGLE_BYTE:
        return bytes([b])
    bit_count = 0
    bit_mask = 0x80
    ll = b
    while ll & bit_mask:
        bit_count += 1
        ll &= 0xFF ^ bit_mask
        bit_mask >>= 1
    size_blob = bytes([ll])
    if bit_count > 1:
        llb = f.read(bit_count - 1)
        if len(llb) != bit_count - 1:
            raise ValueError("bad encoding")
        size_blob += llb
    size = int.from_bytes(size_blob, "big")
    if size >= 0x400000000:
        raise ValueError("blob too large")
    blob = f.read(size)
    if len(blob) != size:
        raise ValueError("bad encoding")
    return bytes([b]) + size_blob[1:] + blob


# instead of parsing the input stream, this function pulls out all the bytes
# that represent on S-expression tree, and returns them. This is more efficient
# than parsing and returning a python S-expression tree.
def sexp_buffer_from_stream(f: typing.BinaryIO) -> bytes:
    ret = io.BytesIO()

    depth = 1
    while depth > 0:
        depth -= 1
        buf, d = _op_consume_sexp(f)
        depth += d
        ret.write(buf)
    return ret.getvalue()


def _atom_from_stream(
    f: typing.BinaryIO, b: int, to_sexp: ToCLVMStorage
) -> CLVMStorage:
    if b == 0x80:
        return to_sexp(b"")
    if b <= MAX_SINGLE_BYTE:
        return to_sexp(bytes([b]))
    bit_count = 0
    bit_mask = 0x80
    while b & bit_mask:
        bit_count += 1
        b &= 0xFF ^ bit_mask
        bit_mask >>= 1
    size_blob = bytes([b])
    if bit_count > 1:
        bb = f.read(bit_count - 1)
        if len(bb) != bit_count - 1:
            raise ValueError("bad encoding")
        size_blob += bb
    size = int.from_bytes(size_blob, "big")
    if size >= 0x400000000:
        raise ValueError("blob too large")
    blob = f.read(size)
    if len(blob) != size:
        raise ValueError("bad encoding")
    return to_sexp(blob)
