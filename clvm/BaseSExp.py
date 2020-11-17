"""
This is the minimal `SExp` type that defines how and where its contents are
stored in the heap. The methods here are the only ones required for `run_program`.
A native implementation of `run_program` should implement this base class.
"""

import typing

# Set this to "1" to do a run-time type check
# This may slow things down a bit

TYPE_CHECK = 0


class BaseSExp:

    atom: typing.Optional[bytes]
    pair: typing.Optional[typing.Tuple["BaseSExp", "BaseSExp"]]
    __slots__ = ["atom", "pair"]

    def __new__(class_, v: "SExpType"):
        if isinstance(v, BaseSExp):
            return v
        if TYPE_CHECK:
            type_ok = (
                isinstance(v, tuple)
                and len(v) == 2
                and isinstance(v[0], BaseSExp)
                and isinstance(v[1], BaseSExp)
            ) or isinstance(v, bytes)
            # uncomment next line for debugging help
            # if not type_ok: breakpoint()
            assert type_ok
        self = super(BaseSExp, class_).__new__(class_)
        if isinstance(v, tuple):
            self.pair = v
            self.atom = None
        else:
            self.atom = v
            self.pair = None
        return self

    def cons(self, right: "BaseSExp"):
        return self.__class__((self, right))


SExpType = typing.Union[bytes, typing.Tuple[BaseSExp, BaseSExp]]
