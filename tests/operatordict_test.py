import unittest

from typing import Dict

from clvm.operators import OperatorProtocol, OperatorDict


class OperatorDictTest(unittest.TestCase):
    def test_operatordict_constructor(self) -> None:
        """Constructing should fail if quote or apply are not specified,
        either by object property or by keyword argument.
        Note that they cannot be specified in the operator dictionary itself.
        """
        # ignoring because apparently it doesn't matter for this test that the types are all wrong
        d: Dict[bytes, OperatorProtocol] = {b"\01": "hello", b"\02": "goodbye"}  # type: ignore [dict-item]
        with self.assertRaises(AssertionError):
            OperatorDict(d)  # type: ignore[call-overload]
        with self.assertRaises(AssertionError):
            OperatorDict(d, apply=b"\01")  # type: ignore[call-overload]
        with self.assertRaises(AssertionError):
            OperatorDict(d, quote=b"\01")  # type: ignore[call-overload]
        o = OperatorDict(d, apply=b"\01", quote=b"\02")
        print(o)
        # Why does the constructed Operator dict contain entries for "apply":1 and "quote":2 ?
        # assert d == o
        self.assertEqual(o.apply_atom, b"\01")
        self.assertEqual(o.quote_atom, b"\02")

        # Test construction from an already existing OperatorDict
        o2 = OperatorDict(o)
        self.assertEqual(o2.apply_atom, b"\01")
        self.assertEqual(o2.quote_atom, b"\02")
