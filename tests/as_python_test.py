import unittest

from clvm import SExp


class AsPythonTest(unittest.TestCase):
    def check_as_python(self, p):
        v = SExp.to(p)
        p1 = v.as_python()
        self.assertEqual(p, p1)

    def test_null(self):
        self.check_as_python(b"")

    def test_single_bytes(self):
        for _ in range(256):
            self.check_as_python(bytes([_]))

    def test_short_lists(self):
        self.check_as_python(b"")
        for _ in range(256):
            for size in range(1, 5):
                self.check_as_python(bytes([_] * size))

    def test_complex(self):
        self.check_as_python((b"", b"foo"))
        self.check_as_python((b"", b"1"))
        self.check_as_python([b"2", (b"", b"1")])
        self.check_as_python([b"", b"2", (b"", b"1")])
        self.check_as_python(
            [b"", b"1", b"2", [b"30", b"40", b"90"], b"600", (b"", b"18")]
        )
