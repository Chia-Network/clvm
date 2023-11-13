from __future__ import annotations

import typing

from typing_extensions import Protocol


class CLVMObjectLike(Protocol):
    # It's not clear if it is possible to express the exclusivity without maybe
    # restructuring all the classes.
    # TODO: can we make these read only?
    atom: typing.Optional[bytes]
    pair: typing.Optional[typing.Tuple[CLVMObjectLike, CLVMObjectLike]]


_T_CLVMObject = typing.TypeVar("_T_CLVMObject", bound="CLVMObject")


class CLVMObject:
    """
    This class implements the CLVM Object protocol in the simplest possible way,
    by just having an "atom" and a "pair" field
    """

    atom: typing.Optional[bytes]

    # this is always a 2-tuple of an object implementing the CLVM object
    # protocol.
    pair: typing.Optional[typing.Tuple[CLVMObjectLike, CLVMObjectLike]]
    __slots__ = ["atom", "pair"]

    @staticmethod
    def __new__(
        class_: typing.Type[_T_CLVMObject],
        # TODO: which?  review?
        # v: typing.Union[CLVMObject, CLVMObjectLike, typing.Tuple[CLVMObject, CLVMObject], bytes],
        v: typing.Union[CLVMObjectLike, bytes],
    ) -> _T_CLVMObject:
        if isinstance(v, class_):
            return v
        self = super(CLVMObject, class_).__new__(class_)
        if isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError("tuples must be of size 2, cannot create CLVMObject from: %s" % str(v))
            self.pair = v
            self.atom = None
        else:
            self.atom = v
            self.pair = None
        return self
