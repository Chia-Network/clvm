import unittest

from clvm.operators import (OPERATOR_LOOKUP, KEYWORD_TO_ATOM)
from clvm.EvalError import EvalError
from clvm import SExp

class OperatorsTest(unittest.TestCase):

    def setUp(self):
        self.handler_called = False

    def unknown_handler(self, name, args):
        self.handler_called = True
        self.assertEqual(name, b'unknown-op')
        self.assertEqual(args, SExp.to(1337))
        return 42,SExp.to(b'foobar')

    def test_unknown_op(self):
        self.assertRaises(EvalError, lambda: OPERATOR_LOOKUP(b'unknown-op', SExp.to(1337)))
        OPERATOR_LOOKUP.set_unknown_op_handler(lambda name, args: self.unknown_handler(name, args))
        cost, ret = OPERATOR_LOOKUP(b'unknown-op', SExp.to(1337))
        self.assertTrue(self.handler_called)
        self.assertEqual(cost, 42)
        self.assertEqual(ret, SExp.to(b'foobar'))

    def test_plus(self):
        print(OPERATOR_LOOKUP)
        self.assertEqual(OPERATOR_LOOKUP(KEYWORD_TO_ATOM['+'], SExp.to([3, 4, 5]))[1], SExp.to(12))

