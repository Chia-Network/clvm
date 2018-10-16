
def int_from_bytes(blob):
    size = len(blob)
    if size == 0 or size > 16:
        return 0
    return int.from_bytes(blob, "big", signed=True)


def int_to_bytes(v):
    byte_count = (v.bit_length() + 8) >> 3
    if byte_count > 16:
        raise ValueError("int too large: %d" % v)
    if v == 0:
        return b''
    return v.to_bytes(byte_count, "big", signed=True)
