import typing


class CLVMObject:
    """
    This class implements the CLVM Object protocol in the simplest possible way,
    by just having an "atom" and a "pair" field
    """

    atom: typing.Optional[bytes]

    # this is always a 2-tuple of an object implementing the CLVM object
    # protocol.
    pair: typing.Optional[typing.Tuple[typing.Any, typing.Any]]
    __slots__ = ["atom", "pair"]

    def __new__(class_, v):
        if isinstance(v, CLVMObject):
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
