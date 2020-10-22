def int_from_bytes(blob):
    size = len(blob)
    if size == 0:
        return 0
    return int.from_bytes(blob, "big", signed=True)


def int_to_bytes(v):
    byte_count = (v.bit_length() + 8) >> 3
    if v == 0:
        return b""
    return v.to_bytes(byte_count, "big", signed=True)


def limbs_for_int(v):
    """
    Return the number of bytes required to represent this integer.
    """
    return (v.bit_length() + 7) >> 3
