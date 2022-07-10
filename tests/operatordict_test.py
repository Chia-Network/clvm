import unittest

from clvm.operators import OperatorDict


class OperatorDictTest(unittest.TestCase):
    def test_operatordict_constructor(self) -> None:
        """Constructing should fail if quote or apply are not specified,
           either by object property or by keyword argument.
           Note that they cannot be specified in the operator dictionary itself.
        """
        d = {1: "hello", 2: "goodbye"}
        with self.assertRaises(AttributeError):
            o = OperatorDict(d)
        with self.assertRaises(AttributeError):
            o = OperatorDict(d, apply=1)
        with self.assertRaises(AttributeError):
            o = OperatorDict(d, quote=1)
        o = OperatorDict(d, apply=1, quote=2)
        print(o)
        # Why does the constructed Operator dict contain entries for "apply":1 and "quote":2 ?
        # assert d == o
        self.assertEqual(o.apply_atom, 1)
        self.assertEqual(o.quote_atom, 2)

        # Test construction from an already existing OperatorDict
        o2 = OperatorDict(o)
        self.assertEqual(o2.apply_atom, 1)
        self.assertEqual(o2.quote_atom, 2)
