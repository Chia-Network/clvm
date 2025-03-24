import unittest
from typing import Tuple

from clvm.operators import (
    OPERATOR_LOOKUP,
    KEYWORD_TO_ATOM,
    default_unknown_op,
    OperatorDict,
)
from clvm.EvalError import EvalError
from clvm.SExp import SExp
from clvm.costs import CONCAT_BASE_COST


class OperatorsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.handler_called = False

    def unknown_handler(self, name: bytes, args: SExp) -> Tuple[int, SExp]:
        self.handler_called = True
        self.assertEqual(name, b"\xff\xff1337")
        self.assertEqual(args, SExp.to(1337))
        return 42, SExp.to(b"foobar")

    def test_unknown_op(self) -> None:
        self.assertRaises(
            EvalError, lambda: OPERATOR_LOOKUP(b"\xff\xff1337", SExp.to(1337))
        )
        od = OperatorDict(
            OPERATOR_LOOKUP,
            unknown_op_handler=lambda name, args: self.unknown_handler(name, args),
        )
        cost, ret = od(b"\xff\xff1337", SExp.to(1337))
        self.assertTrue(self.handler_called)
        self.assertEqual(cost, 42)
        self.assertEqual(ret, SExp.to(b"foobar"))

    def test_plus(self) -> None:
        print(OPERATOR_LOOKUP)
        self.assertEqual(
            OPERATOR_LOOKUP(KEYWORD_TO_ATOM["+"], SExp.to([3, 4, 5]))[1], SExp.to(12)
        )

    def test_unknown_op_reserved(self) -> None:
        # any op that starts with ffff is reserved, and results in a hard
        # failure
        with self.assertRaises(EvalError):
            default_unknown_op(b"\xff\xff", SExp.null())

        for suffix in [b"\xff", b"0", b"\x00", b"\xcc\xcc\xfe\xed\xfa\xce"]:
            with self.assertRaises(EvalError):
                default_unknown_op(b"\xff\xff" + suffix, SExp.null())

        with self.assertRaises(EvalError):
            # an empty atom is not a valid opcode
            default_unknown_op(b"", SExp.null())

        # a single ff is not sufficient to be treated as a reserved opcode
        self.assertEqual(
            default_unknown_op(b"\xff", SExp.null()), (CONCAT_BASE_COST, SExp.null())
        )

        # leading zeroes count, and this does not count as a ffff-prefix
        # the cost is 0xffff00 = 16776960
        self.assertEqual(
            default_unknown_op(b"\x00\xff\xff\x00\x00", SExp.null()),
            (16776961, SExp.null()),
        )

    def test_unknown_ops_last_bits(self) -> None:
        # The last byte is ignored for no-op unknown ops
        for suffix in [b"\x3f", b"\x0f", b"\x00", b"\x2c"]:
            # the cost is unchanged by the last byte
            self.assertEqual(
                default_unknown_op(b"\x3c" + suffix, SExp.null()), (61, SExp.null())
            )
