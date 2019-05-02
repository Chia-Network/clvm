
def to_bytes(v, length, byteorder="big"):
    """For python 3, which has a native implementation of this function."""
    return v.to_bytes(length, byteorder=byteorder)


def from_bytes(bytes, byteorder="big", signed=False):
    """For python 3, which has a native implementation of this function."""
    return int.from_bytes(bytes, byteorder=byteorder, signed=signed)
