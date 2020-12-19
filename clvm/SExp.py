import io
import typing

from blspy import G1Element

from .as_python import as_python
from .CLVMObject import CLVMObject, SExpType

from .EvalError import EvalError

from .casts import (
    int_from_bytes,
    int_to_bytes,
)
from .serialize import sexp_to_stream


CastableType = typing.Union[
    "SExp",
    CLVMObject,
    bytes,
    int,
    None,
    SExpType,
    G1Element,
    typing.Tuple[typing.Any, typing.Any],
]

NULL = b""


def to_sexp_type(
    v: CastableType,
) -> SExpType:
    stack = [v]
    ops = [(0, None)]  # convert

    while len(ops) > 0:
        op, target = ops.pop()
        # convert value
        if op == 0:
            v = stack.pop()
            if isinstance(v, tuple):
                if len(v) != 2:
                    raise ValueError("can't cast tuple of size %d" % len(v))
                left, right = v
                target = len(stack)
                stack.append((left, right))
                if type(right) != CLVMObject:
                    stack.append(right)
                    ops.append((2, target))  # set right
                    ops.append((0, None))  # convert
                if type(left) != CLVMObject:
                    stack.append(left)
                    ops.append((1, target))  # set left
                    ops.append((0, None))  # convert
                continue
            if isinstance(v, CLVMObject):
                stack.append(v.pair or v.atom)
                continue
            if isinstance(v, bytes):
                stack.append(v)
                continue
            if isinstance(v, str):
                stack.append(v.encode())
                continue
            if isinstance(v, int):
                stack.append(int_to_bytes(v))
                continue
            if isinstance(v, G1Element):
                stack.append(bytes(v))
                continue
            if v is None:
                stack.append(NULL)
                continue
            if v == []:
                stack.append(NULL)
                continue

            if hasattr(v, "__iter__"):
                target = len(stack)
                stack.append(NULL)
                for _ in v:
                    stack.append(_)
                    ops.append((3, target))  # prepend list
                    # we only need to convert if it's not already the right
                    # type
                    if type(_) != CLVMObject:
                        ops.append((0, None))  # convert
                continue

            raise ValueError("can't cast to CLVMObject: %s" % v)
        if op == 1:  # set left
            stack[target] = (CLVMObject(stack.pop()), stack[target][1])
            continue
        if op == 2:  # set right
            stack[target] = (stack[target][0], CLVMObject(stack.pop()))
            continue
        if op == 3:  # prepend list
            stack[target] = (CLVMObject(stack.pop()), CLVMObject(stack[target]))
            continue
    # there's exactly one item left at this point
    if len(stack) != 1:
        raise ValueError("internal error")
    return stack[0]


class SExp(CLVMObject):
    true: "SExp"
    false: "SExp"
    __null__: "SExp"

    def as_pair(self):
        pair = self.pair
        if pair is None:
            return pair
        return (self.to(pair[0]), self.to(pair[1]))

    def as_atom(self):
        return self.atom

    def listp(self):
        return self.pair is not None

    def nullp(self):
        return self.atom == b""

    def as_int(self):
        return int_from_bytes(self.atom)

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    @classmethod
    def to(class_, v: CastableType):
        if isinstance(v, class_):
            return v
        v1 = to_sexp_type(v)
        return class_(v1)

    def cons(self, right: "CLVMObject"):
        s = (self, right)
        return self.to(s)

    def first(self):
        pair = self.pair
        if pair:
            return self.to(pair[0])
        raise EvalError("first of non-cons", self)

    def rest(self):
        pair = self.pair
        if pair:
            return self.to(pair[1])
        raise EvalError("rest of non-cons", self)

    @classmethod
    def null(class_):
        return class_.__null__

    def as_iter(self):
        v = self
        while not v.nullp():
            yield v.first()
            v = v.rest()

    def __eq__(self, other: CastableType):
        try:
            other = self.to(other)
        except ValueError:
            return False
        to_compare_stack = [(self, other)]
        while to_compare_stack:
            s1, s2 = to_compare_stack.pop()
            p1 = s1.as_pair()
            if p1:
                p2 = s2.as_pair()
                if p2:
                    to_compare_stack.append((p1[0], p2[0]))
                    to_compare_stack.append((p1[1], p2[1]))
                else:
                    return False
            elif s2.as_pair() or s1.as_atom() != s2.as_atom():
                return False
        return True

    def list_len(self):
        v = self
        size = 0
        while v.listp():
            size += 1
            v = v.rest()
        return size

    def as_python(self):
        return as_python(self)

    def __str__(self):
        return self.as_bin().hex()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self))


SExp.false = SExp.__null__ = SExp(b"")
SExp.true = SExp(b"\1")
