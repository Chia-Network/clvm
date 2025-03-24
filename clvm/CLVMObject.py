from __future__ import annotations

import typing


class CLVMStorage(typing.Protocol):
    # It's not clear if it is possible to express the exclusivity without maybe
    # restructuring all the classes, such as having a separate instance for each
    # of the atom and pair cases and hinting a union of a protocol of each type.
    atom: typing.Optional[bytes]
    pair: typing.Optional[PairType]


PairType = typing.Tuple[CLVMStorage, CLVMStorage]


_T_CLVMObject = typing.TypeVar("_T_CLVMObject", bound="CLVMObject")


class CLVMObject:
    """
    This class implements the CLVM Object protocol in the simplest possible way,
    by just having an "atom" and a "pair" field
    """

    atom: typing.Optional[bytes]

    # this is always a 2-tuple of an object implementing the CLVM object
    # protocol.
    pair: typing.Optional[PairType]
    __slots__ = ["atom", "pair"]

    @staticmethod
    def __new__(
        class_: typing.Type[_T_CLVMObject],
        v: typing.Union[_T_CLVMObject, bytes, PairType],
    ) -> _T_CLVMObject:
        if isinstance(v, class_):
            return v
        # mypy does not realize that the isinstance check is type narrowing like this
        narrowed_v: typing.Union[bytes, PairType] = v  # type: ignore[assignment]

        self = super(CLVMObject, class_).__new__(class_)
        if isinstance(narrowed_v, tuple):
            if len(narrowed_v) != 2:
                raise ValueError(
                    "tuples must be of size 2, cannot create CLVMObject from: %s"
                    % str(narrowed_v)
                )
            self.pair = narrowed_v
            self.atom = None
        else:
            self.atom = narrowed_v
            self.pair = None
        return self
