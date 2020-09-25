import io
import unittest

from clvm import to_sexp_f
from clvm.serialize import sexp_from_stream


TEXT = b"the quick brown fox jumps over the lazy dogs"


class SerializeTest(unittest.TestCase):
    def check_serde(self, s):
        v = to_sexp_f(s)
        b = v.as_bin()
        v1 = sexp_from_stream(io.BytesIO(b), to_sexp_f)
        if v != v1:
            print("%s: %d %s %s" % (v, len(b), b, v1))
            breakpoint()
            b = v.as_bin()
            v1 = sexp_from_stream(io.BytesIO(b), to_sexp_f)
        self.assertEqual(v, v1)

    def test_empty_string(self):
        self.check_serde(b"")

    def test_single_bytes(self):
        for _ in range(256):
            self.check_serde(bytes([_]))

    def test_short_lists(self):
        self.check_serde([])
        for _ in range(0, 2048, 8):
            for size in range(1, 5):
                self.check_serde([_] * size)

    def test_cons_box(self):
        self.check_serde((None, None))
        self.check_serde((None, [1, 2, 30, 40, 600, (None, 18)]))
        self.check_serde((100, (TEXT, (30, (50, (90, (TEXT, TEXT + TEXT)))))))

    def test_long_blobs(self):
        text = TEXT * 300
        for _, t in enumerate(text):
            t1 = text[:_]
            self.check_serde(t1)

    def test_very_long_blobs(self):
        for size in [0x40, 0x2000, 0x100000, 0x8000000]:
            count = size // len(TEXT)
            text = TEXT * count
            assert len(text) < size
            self.check_serde(text)
            text = TEXT * (count + 1)
            assert len(text) > size
            self.check_serde(text)
