import unittest

from clvm import SExp
from clvm.CLVMObject import CLVMObject


def validate_sexp(sexp):
    validate_stack = [sexp]
    while validate_stack:
        v = validate_stack.pop()
        assert isinstance(v, SExp)
        if v.pair:
            v1, v2 = v.pair
            assert isinstance(v1, CLVMObject)
            assert isinstance(v2, CLVMObject)
            s1, s2 = v.as_pair()
            validate_stack.append(s1)
            validate_stack.append(s2)
        else:
            assert isinstance(v.atom, bytes)


class ToSExpTest(unittest.TestCase):
    def test_cast_1(self):
        # this was a problem in `clvm_tools` and is included
        # to prevent regressions
        sexp = SExp.to(b"foo")
        t1 = sexp.to([1, sexp])
        validate_sexp(t1)
