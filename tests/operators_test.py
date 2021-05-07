import unittest

from clvm.chia_dialect import chia_dialect_info
from clvm.handle_unknown_op import handle_unknown_op_softfork_ready
from clvm.dialect import ChainableMultiOpFn
from clvm.operators import KEYWORD_TO_ATOM
from clvm.EvalError import EvalError
from clvm import SExp
from clvm.costs import CONCAT_BASE_COST

OPERATOR_LOOKUP = ChainableMultiOpFn(
    chia_dialect_info().opcode_lookup, handle_unknown_op_softfork_ready
)


class OperatorsTest(unittest.TestCase):
    def setUp(self):
        self.handler_called = False

    def unknown_handler(self, name, args, _max_cost):
        self.handler_called = True
        self.assertEqual(name, b"\xff\xff1337")
        self.assertEqual(args, SExp.to(1337))
        return 42, SExp.to(b"foobar")

    def test_unknown_op(self):
        self.assertRaises(
            EvalError, lambda: OPERATOR_LOOKUP(b"\xff\xff1337", SExp.to(1337), None)
        )
        od = ChainableMultiOpFn(chia_dialect_info().opcode_lookup, self.unknown_handler)
        cost, ret = od(b"\xff\xff1337", SExp.to(1337), None)
        self.assertTrue(self.handler_called)
        self.assertEqual(cost, 42)
        self.assertEqual(ret, SExp.to(b"foobar"))

    def test_plus(self):
        print(OPERATOR_LOOKUP)
        self.assertEqual(
            OPERATOR_LOOKUP(KEYWORD_TO_ATOM["+"], SExp.to([3, 4, 5]), None)[1],
            SExp.to(12),
        )

    def test_unknown_op_reserved(self):

        # any op that starts with ffff is reserved, and results in a hard
        # failure
        with self.assertRaises(EvalError):
            handle_unknown_op_softfork_ready(b"\xff\xff", SExp.null(), max_cost=None)

        for suffix in [b"\xff", b"0", b"\x00", b"\xcc\xcc\xfe\xed\xfa\xce"]:
            with self.assertRaises(EvalError):
                handle_unknown_op_softfork_ready(
                    b"\xff\xff" + suffix, SExp.null(), max_cost=None
                )

        with self.assertRaises(EvalError):
            # an empty atom is not a valid opcode
            self.assertEqual(
                handle_unknown_op_softfork_ready(b"", SExp.null(), max_cost=None),
                (1, SExp.null()),
            )

        # a single ff is not sufficient to be treated as a reserved opcode
        self.assertEqual(
            handle_unknown_op_softfork_ready(b"\xff", SExp.null(), max_cost=None),
            (CONCAT_BASE_COST, SExp.null()),
        )

        # leading zeroes count, and this does not count as a ffff-prefix
        # the cost is 0xffff00 = 16776960
        self.assertEqual(
            handle_unknown_op_softfork_ready(
                b"\x00\xff\xff\x00\x00", SExp.null(), max_cost=None
            ),
            (16776961, SExp.null()),
        )

    def test_unknown_ops_last_bits(self):

        # The last byte is ignored for no-op unknown ops
        for suffix in [b"\x3f", b"\x0f", b"\x00", b"\x2c"]:
            # the cost is unchanged by the last byte
            self.assertEqual(
                handle_unknown_op_softfork_ready(b"\x3c" + suffix, SExp.null(), max_cost=None),
                (61, SExp.null()),
            )
