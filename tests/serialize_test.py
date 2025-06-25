import gzip
import io
import unittest
from typing import Optional

import pytest

from clvm import to_sexp_f
from clvm.SExp import CastableType, SExp
from clvm.serialize import (
    MAX_SAFE_BYTES,
    _atom_from_stream,
    sexp_from_stream,
    sexp_buffer_from_stream,
    atom_to_byte_iterator,
    sexp_to_stream,
)


TEXT = b"the quick brown fox jumps over the lazy dogs"


class InfiniteStream(io.BytesIO):
    def read(self, n: Optional[int] = -1) -> bytes:
        result = super().read(n)

        if n is not None and n > 0:
            fill_needed = n - len(result)
            result += b" " * fill_needed

        return result


class LargeAtom:
    def __len__(self) -> int:
        return 0x400000001


def has_backrefs(blob: bytes) -> bool:
    """
    Return `True` iff blob has a backref in it.
    """
    f = io.BytesIO(blob)
    obj_count = 1
    while obj_count > 0:
        b = f.read(1)[0]
        if b == 0xFE:
            return True
        if b == 0xFF:
            obj_count += 1
        else:
            _atom_from_stream(f, b)
            obj_count -= 1
    return False


class SerializeTest(unittest.TestCase):
    def check_serde(self, s: CastableType) -> bytes:
        v = to_sexp_f(s)
        b = v.as_bin()
        f = io.BytesIO()
        v1 = sexp_from_stream(io.BytesIO(b), to_sexp_f)
        if v != v1:
            print("%s: %d %r %s" % (v, len(b), b, v1))
            breakpoint()
            b = v.as_bin()
            v1 = sexp_from_stream(io.BytesIO(b), to_sexp_f)
        self.assertEqual(v, v1)
        sexp_to_stream(v1, f)
        length = len(f.getvalue())
        assert f.getbuffer() == b
        # this copies the bytes that represent a single s-expression, just to
        # know where the message ends. It doesn't build a python representaion
        # of it
        buf = sexp_buffer_from_stream(io.BytesIO(b))
        self.assertEqual(buf, b)

        # now turn on backrefs and make sure everything still works

        b2 = v.as_bin(allow_backrefs=True)
        self.assertTrue(len(b2) <= len(b))
        if has_backrefs(b2) or len(b2) < len(b):
            # if we have any backrefs, ensure they actually save space
            self.assertTrue(len(b2) < len(b))
            print(
                "%d bytes before %d after %d saved"
                % (len(b), len(b2), len(b) - len(b2))
            )
            io_b2 = io.BytesIO(b2)
            self.assertRaises(ValueError, lambda: sexp_from_stream(io_b2, to_sexp_f))
            io_b2 = io.BytesIO(b2)
            v2 = sexp_from_stream(io_b2, to_sexp_f, allow_backrefs=True)
            self.assertEqual(v2, s)
            b3 = v2.as_bin()
            self.assertEqual(b, b3)
        with pytest.raises(ValueError, match="SExp exceeds maximum size"):
            f = io.BytesIO()
            sexp_to_stream(v1, f, max_size=length-1)
        f = io.BytesIO()
        sexp_to_stream(v1, f, max_size=length)
        return b2

    def test_zero(self) -> None:
        v = to_sexp_f(b"\x00")
        self.assertEqual(v.as_bin(), b"\x00")

    def test_empty(self) -> None:
        v = to_sexp_f(b"")
        self.assertEqual(v.as_bin(), b"\x80")

    def test_empty_string(self) -> None:
        self.check_serde(b"")

    def test_single_bytes(self) -> None:
        for _ in range(256):
            self.check_serde(bytes([_]))

    def test_short_lists(self) -> None:
        self.check_serde([])
        for _ in range(0, 2048, 8):
            for size in range(1, 5):
                self.check_serde([_] * size)

    def test_cons_box(self) -> None:
        self.check_serde((None, None))
        a: CastableType = (None, 18)
        b: CastableType = [1, 2, 30, 40, 600, a]
        c: CastableType = (None, b)
        self.check_serde(c)
        self.check_serde((100, (TEXT, (30, (50, (90, (TEXT, TEXT + TEXT)))))))

    def test_long_blobs(self) -> None:
        text = TEXT * 300
        for _, t in enumerate(text):
            t1 = text[:_]
            self.check_serde(t1)

    def test_blob_limit(self) -> None:
        with self.assertRaises(ValueError):
            # Specifically substituting another type that is sufficiently similar to
            # the expected bytes for this test.
            for _ in atom_to_byte_iterator(LargeAtom()):  # type: ignore[arg-type]
                pass

    def test_very_long_blobs(self) -> None:
        for size in [0x40, 0x2000, 0x100000, 0x8000000]:
            count = size // len(TEXT)
            text = TEXT * count
            assert len(text) < size
            if len(text) >= MAX_SAFE_BYTES:
                with pytest.raises(ValueError, match="SExp exceeds maximum size"):
                    self.check_serde(text)
            else:
                self.check_serde(text)
            text = TEXT * (count + 1)
            assert len(text) > size
            if len(text) >= MAX_SAFE_BYTES:
                with pytest.raises(ValueError, match="SExp exceeds maximum size"):
                    self.check_serde(text)
            else:
                self.check_serde(text)

    def test_very_deep_tree(self) -> None:
        blob = b"a"
        for depth in [10, 100, 1000, 10000, 100000]:
            s = to_sexp_f(blob)
            for _ in range(depth):
                s = to_sexp_f((s, blob))
            self.check_serde(s)

    def test_deserialize_empty(self) -> None:
        bytes_in = b""
        with self.assertRaises(ValueError):
            sexp_from_stream(io.BytesIO(bytes_in), to_sexp_f)

        with self.assertRaises(ValueError):
            sexp_buffer_from_stream(io.BytesIO(bytes_in))

    def test_deserialize_truncated_size(self) -> None:
        # fe means the total number of bytes in the length-prefix is 7
        # one for each bit set. 5 bytes is too few
        bytes_in = b"\xfe    "
        with self.assertRaises(ValueError):
            sexp_from_stream(io.BytesIO(bytes_in), to_sexp_f)

        with self.assertRaises(ValueError):
            sexp_buffer_from_stream(io.BytesIO(bytes_in))

    def test_deserialize_truncated_blob(self) -> None:
        # this is a complete length prefix. The blob is supposed to be 63 bytes
        # the blob itself is truncated though, it's less than 63 bytes
        bytes_in = b"\xbf   "

        with self.assertRaises(ValueError):
            sexp_from_stream(io.BytesIO(bytes_in), to_sexp_f)

        with self.assertRaises(ValueError):
            sexp_buffer_from_stream(io.BytesIO(bytes_in))

    def test_deserialize_large_blob(self) -> None:
        # this length prefix is 7 bytes long, the last 6 bytes specifies the
        # length of the blob, which is 0xffffffffffff, or (2^48 - 1)
        # we don't support blobs this large, and we should fail immediately when
        # exceeding the max blob size, rather than trying to read this many
        # bytes from the stream
        bytes_in = b"\xfe" + b"\xff" * 6

        with self.assertRaises(ValueError):
            sexp_from_stream(InfiniteStream(bytes_in), to_sexp_f)

        with self.assertRaises(ValueError):
            sexp_buffer_from_stream(InfiniteStream(bytes_in))

    def test_deserialize_generator(self) -> None:
        blob = gzip.GzipFile("tests/generator.bin.gz").read()
        s = sexp_from_stream(io.BytesIO(blob), to_sexp_f)
        b = self.check_serde(s)
        assert len(b) == 19124

    def test_deserialize_bomb(self) -> None:
        def make_bomb(depth: int) -> SExp:
            bomb = to_sexp_f(TEXT)
            for _ in range(depth):
                bomb = to_sexp_f((bomb, bomb))
            return bomb

        bomb_10 = make_bomb(10)
        b10_1 = bomb_10.as_bin(allow_backrefs=False)
        b10_2 = bomb_10.as_bin(allow_backrefs=True)
        self.assertEqual(len(b10_1), 47103)
        self.assertEqual(len(b10_2), 75)

        bomb_20 = make_bomb(20)
        with pytest.raises(ValueError, match="SExp exceeds maximum size"):
            bomb_20.as_bin(allow_backrefs=False)
        b20_2 = bomb_20.as_bin(allow_backrefs=True)
        self.assertEqual(len(b20_2), 105)

        bomb_30 = make_bomb(30)
        with pytest.raises(ValueError, match="SExp exceeds maximum size"):
            bomb_30.as_bin(allow_backrefs=False)
        b30_2 = bomb_30.as_bin(allow_backrefs=True)

        self.assertEqual(len(b30_2), 135)

    def test_specific_tree(self) -> None:
        sexp1 = to_sexp_f((("AAA", "BBB"), ("CCC", "AAA")))
        serialized_sexp1_v1 = sexp1.as_bin(allow_backrefs=False)
        serialized_sexp1_v2 = sexp1.as_bin(allow_backrefs=True)
        self.assertEqual(len(serialized_sexp1_v1), 19)
        self.assertEqual(len(serialized_sexp1_v2), 17)
        deserialized_sexp1_v1 = sexp_from_stream(
            io.BytesIO(serialized_sexp1_v1), to_sexp_f, allow_backrefs=False
        )
        deserialized_sexp1_v2 = sexp_from_stream(
            io.BytesIO(serialized_sexp1_v2), to_sexp_f, allow_backrefs=True
        )
        self.assertTrue(deserialized_sexp1_v1 == deserialized_sexp1_v2)
