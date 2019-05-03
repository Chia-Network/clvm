import io
import unittest

from opacity.Var import Var
from opacity.SExp import sexp_from_stream, to_sexp_f


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
        self.check_serde(b'')

    def test_single_bytes(self):
        for _ in range(256):
            self.check_serde(bytes([_]))

    def test_short_lists(self):
        self.check_serde([])
        for _ in range(1024):
            for size in range(1, 5):
                self.check_serde([_] * size)

    def test_vars(self):
        for _ in range(100000):
            self.check_serde(Var(_))
        for _ in range(32):
            self.check_serde(Var((1 << _)-1))
        for _ in range(33):
            self.check_serde(Var((1 << _) + (1 << (_//3))))

    def test_long_blobs(self):
        text = b"the quick brown fox jumps over the lazy dogs" * 30
        for _, t in enumerate(text):
            t1 = text[:_]
            self.check_serde(t1)
