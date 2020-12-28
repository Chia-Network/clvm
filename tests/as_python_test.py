import unittest

from clvm import SExp
from clvm.CLVMObject import CLVMObject
from blspy import G1Element
from clvm.EvalError import EvalError


class dummy_class:
    def __init__(self):
        self.i = 0

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

    def test_int(self):
        v = SExp.to(42)
        self.assertEqual(v.atom, b"\x2a")

    def test_none(self):
        v = SExp.to(None)
        self.assertEqual(v.atom, b"")

    def test_empty_list(self):
        v = SExp.to([])
        self.assertEqual(v.atom, b"")

    def test_g1element(self):
        b = b"\xb3\xb8\xac\x53\x7f\x4f\xd6\xbd\xe9\xb2" \
            b"\x62\x21\xd4\x9b\x54\xb1\x7a\x50\x6b\xe1\x47\x34\x7d\xae\x5d" \
            b"\x08\x1c\x0a\x65\x72\xb6\x11\xd8\x48\x4e\x33\x8f\x34\x32\x97" \
            b"\x1a\x98\x23\x97\x6c\x6a\x23\x2b"
        v = SExp.to(G1Element(b))
        self.assertEqual(v.atom, b)

    def test_complex(self):
        self.check_as_python((b"", b"foo"))
        self.check_as_python((b"", b"1"))
        self.check_as_python([b"2", (b"", b"1")])
        self.check_as_python([b"", b"2", (b"", b"1")])
        self.check_as_python(
            [b"", b"1", b"2", [b"30", b"40", b"90"], b"600", (b"", b"18")]
        )

    def test_listp(self):
        self.assertEqual(SExp.to(42).listp(), False);
        self.assertEqual(SExp.to(b"").listp(), False);
        self.assertEqual(SExp.to(b"1337").listp(), False);

        self.assertEqual(SExp.to((1337, 42)).listp(), True);
        self.assertEqual(SExp.to([1337, 42]).listp(), True);

    def test_nullp(self):
        self.assertEqual(SExp.to(b"").nullp(), True)
        self.assertEqual(SExp.to(b"1337").nullp(), False)
        self.assertEqual(SExp.to((b"", b"")).nullp(), False)

    def test_constants(self):
        self.assertEqual(SExp.__null__.nullp(), True)
        self.assertEqual(SExp.null().nullp(), True)
        self.assertEqual(SExp.true, True)
        self.assertEqual(SExp.false, False)

    def test_list_len(self):
        v = SExp.to(42);
        for i in range(100):
            self.assertEqual(v.list_len(), i)
            v = SExp.to((42, v))
        self.assertEqual(v.list_len(), 100)

    def test_as_int(self):
        self.assertEqual(SExp.to(b'\x80').as_int(), -128)
        self.assertEqual(SExp.to(b'\xff').as_int(), -1)
        self.assertEqual(SExp.to(b'\x00\x80').as_int(), 128)
        self.assertEqual(SExp.to(b'\x00\xff').as_int(), 255)

    def test_cons(self):
        # list
        self.assertEqual(SExp.to(b'\x01').cons(SExp.to(b'\x02').cons(SExp.null())).as_python(), [b'\x01', b'\x02'])
        # cons-box of two values
        self.assertEqual(SExp.to(b'\x01').cons(SExp.to(b'\x02').as_python()), (b'\x01', b'\x02'))

    def test_string(self):
        self.assertEqual(SExp.to('foobar').as_atom(), b'foobar')

    def test_deep_recursion(self):
        d = b'2'
        for i in range(1000):
            d = [d]
        v = SExp.to(d)
        for i in range(1000):
            self.assertEqual(v.as_pair()[1].as_atom(), SExp.null())
            v = v.as_pair()[0]
            d = d[0]

        self.assertEqual(v.as_atom(), b'2')
        self.assertEqual(d, b'2')

    def test_long_linked_list(self):
        d = b''
        for i in range(1000):
            d = (b'2', d)
        v = SExp.to(d)
        for i in range(1000):
            self.assertEqual(v.as_pair()[0].as_atom(), d[0])
            v = v.as_pair()[1]
            d = d[1]

        self.assertEqual(v.as_atom(), SExp.null())
        self.assertEqual(d, b'')

    def test_long_list(self):
        d = [1337] * 1000
        v = SExp.to(d)
        for i in range(1000 - 1):
            self.assertEqual(v.as_pair()[0].as_int(), d[i])
            v = v.as_pair()[1]

        self.assertEqual(v.as_atom(), SExp.null())

    def test_invalid_type(self):
        self.assertRaises(ValueError, lambda: SExp.to(dummy_class))

    def test_invalid_tuple(self):
        self.assertRaises(ValueError, lambda: SExp.to((dummy_class, dummy_class)))
        self.assertRaises(ValueError, lambda: SExp.to((dummy_class, dummy_class, dummy_class)))

    def test_clvm_object_tuple(self):
        o1 = CLVMObject(b"foo")
        o2 = CLVMObject(b"bar")
        self.assertEqual(SExp.to((o1, o2)), (o1, o2))

    def test_as_iter(self):
        val = list(SExp.to((1, (2, (3, (4, b""))))).as_iter())
        self.assertEqual(val, [1, 2, 3, 4])

        val = list(SExp.to(b"").as_iter())
        self.assertEqual(val, [])

        val = list(SExp.to((1, b"")).as_iter())
        self.assertEqual(val, [1])

        # these fail because the lists are not null-terminated
        self.assertRaises(EvalError, lambda: list(SExp.to(1).as_iter()))
        self.assertRaises(EvalError, lambda: list(SExp.to((1, (2, (3, (4, 5))))).as_iter()))
