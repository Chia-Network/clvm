# decoding:
# read a byte
# if it's 0x80, it's nil (which might be same as 0)
# if it's 0xfe, it's a back-reference. Read an atom, and treat it as a path in the cache tree.
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

import io
import typing

from .read_cache_lookup import ReadCacheLookup
from .object_cache import ObjectCache, treehash, serialized_length

from .CLVMObject import CLVMStorage

MAX_SINGLE_BYTE = 0x7F
BACK_REFERENCE = 0xFE
CONS_BOX_MARKER = 0xFF

MAX_SAFE_BYTES = 2_000_000

T = typing.TypeVar("T")
_T_CLVMStorage = typing.TypeVar("_T_CLVMStorage", bound=CLVMStorage)

CS = typing.TypeVar("CS", bound=CLVMStorage)

ToCLVMStorage = typing.Callable[
    [typing.Union[CLVMStorage, bytes, typing.Tuple[CLVMStorage, CLVMStorage]]],
    _T_CLVMStorage,
]

ValStackType = CLVMStorage

OpCallable = typing.Callable[
    ["OpStackType[T]", ValStackType, typing.BinaryIO, ToCLVMStorage[T]], ValStackType
]

OpStackType = typing.List[OpCallable[T]]


def sexp_to_byte_iterator(
    sexp: CLVMStorage, *, allow_backrefs: bool = False
) -> typing.Iterator[bytes]:
    if allow_backrefs:
        yield from sexp_to_byte_iterator_with_backrefs(sexp)
        return

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


def sexp_to_byte_iterator_with_backrefs(sexp: CLVMStorage) -> typing.Iterator[bytes]:
    # in `read_op_stack`:
    #  "P" = "push"
    #  "C" = "pop two objects, create and push a new cons with them"

    read_op_stack = ["P"]

    write_stack = [sexp]

    read_cache_lookup = ReadCacheLookup()

    thc = ObjectCache(treehash)
    slc = ObjectCache(serialized_length)

    while write_stack:
        node_to_write = write_stack.pop()
        op = read_op_stack.pop()
        assert op == "P"

        node_serialized_length = slc.get(node_to_write)

        node_tree_hash = thc.get(node_to_write)
        path = read_cache_lookup.find_path(node_tree_hash, node_serialized_length)
        if path:
            yield bytes([BACK_REFERENCE])
            yield from atom_to_byte_iterator(path)
            read_cache_lookup.push(node_tree_hash)
        elif node_to_write.pair:
            left, right = node_to_write.pair
            yield bytes([CONS_BOX_MARKER])
            write_stack.append(right)
            write_stack.append(left)
            read_op_stack.append("C")
            read_op_stack.append("P")
            read_op_stack.append("P")
        else:
            atom = node_to_write.atom
            assert atom is not None
            yield from atom_to_byte_iterator(atom)
            read_cache_lookup.push(node_tree_hash)

        while read_op_stack[-1:] == ["C"]:
            read_op_stack.pop()
            read_cache_lookup.pop2_and_cons()


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


def sexp_to_stream(
    sexp: CLVMStorage, f: typing.BinaryIO, *, allow_backrefs: bool = False, max_size: int = MAX_SAFE_BYTES
) -> None:
    for b in sexp_to_byte_iterator(sexp, allow_backrefs=allow_backrefs):
        max_size -= len(b)
        if max_size < 0:
            raise ValueError("SExp exceeds maximum size")
        f.write(b)


def msb_mask(byte: int) -> int:
    byte |= byte >> 1
    byte |= byte >> 2
    byte |= byte >> 4
    return (byte + 1) >> 1


def traverse_path(
    obj: CLVMStorage, path: bytes, to_sexp: ToCLVMStorage[CS]
) -> CLVMStorage:
    path_as_int = int.from_bytes(path, "big")
    if path_as_int == 0:
        return to_sexp(b"")

    while path_as_int > 1:
        if obj.pair is None:
            raise ValueError("path into atom", obj)
        obj = obj.pair[path_as_int & 1]
        path_as_int >>= 1

    return obj


def _op_cons(
    op_stack: OpStackType[CS],
    val_stack: ValStackType,
    f: typing.BinaryIO,
    to_sexp: ToCLVMStorage[CS],
) -> ValStackType:
    assert val_stack.pair is not None
    right, val_stack = val_stack.pair
    assert val_stack.pair is not None
    left, val_stack = val_stack.pair
    new_cons = to_sexp((left, right))
    return to_sexp((new_cons, val_stack))


def _op_read_sexp(
    op_stack: OpStackType[CS],
    val_stack: ValStackType,
    f: typing.BinaryIO,
    to_sexp: ToCLVMStorage[CS],
) -> ValStackType:
    blob = f.read(1)
    if len(blob) == 0:
        raise ValueError("bad encoding")
    b = blob[0]
    if b == CONS_BOX_MARKER:
        op_stack.append(_op_cons)
        op_stack.append(_op_read_sexp)
        op_stack.append(_op_read_sexp)
        return val_stack
    atom_as_sexp = to_sexp(_atom_from_stream(f, b))
    return to_sexp((atom_as_sexp, val_stack))


def _op_read_sexp_allow_backrefs(
    op_stack: OpStackType[CS],
    val_stack: ValStackType,
    f: typing.BinaryIO,
    to_sexp: ToCLVMStorage[CS],
) -> CLVMStorage:
    blob = f.read(1)
    if len(blob) == 0:
        raise ValueError("bad encoding")
    b = blob[0]
    if b == CONS_BOX_MARKER:
        op_stack.append(_op_cons)
        op_stack.append(_op_read_sexp_allow_backrefs)
        op_stack.append(_op_read_sexp_allow_backrefs)
        return val_stack
    if b == BACK_REFERENCE:
        blob = f.read(1)
        if len(blob) == 0:
            raise ValueError("bad encoding")
        path = _atom_from_stream(f, blob[0])
        backref = traverse_path(val_stack, path, to_sexp)
        return to_sexp((backref, val_stack))
    atom_as_sexp = to_sexp(_atom_from_stream(f, b))
    return to_sexp((atom_as_sexp, val_stack))


def sexp_from_stream(
    f: typing.BinaryIO, to_sexp: ToCLVMStorage[CS], *, allow_backrefs: bool = False
) -> CS:
    op_stack: OpStackType[CS] = [
        _op_read_sexp_allow_backrefs if allow_backrefs else _op_read_sexp
    ]
    val_stack: ValStackType = to_sexp(b"")

    while op_stack:
        func = op_stack.pop()
        val_stack = func(op_stack, val_stack, f, to_sexp)
    assert val_stack.pair is not None
    return to_sexp(val_stack.pair[0])


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


def _atom_from_stream(f: typing.BinaryIO, b: int) -> bytes:
    if b == 0x80:
        return b""
    if b <= MAX_SINGLE_BYTE:
        return bytes([b])
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
    return blob
