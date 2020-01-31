from .ecdsa.bls12_381 import bls12_381_generator


def int_from_bytes(blob):
    size = len(blob)
    if size == 0 or size > 32:
        return 0
    return int.from_bytes(blob, "big", signed=True)


def int_to_bytes(v):
    byte_count = (v.bit_length() + 8) >> 3
    if byte_count > 32:
        raise ValueError("int too large: %d" % v)
    if v == 0:
        return b''
    return v.to_bytes(byte_count, "big", signed=True)


BLS12_381_POINT_BYTE_COUNT = (bls12_381_generator[0].bit_length() + 7) // 8


def bls12_381_from_bytes(blob):
    if blob == b'':
        return bls12_381_generator.infinity()
    ba = bytearray(blob)
    ba[0] &= 0x7f
    hi_bit = blob[0] & 0x80
    x = int.from_bytes(ba, byteorder="big", signed=False)
    try:
        points = bls12_381_generator.points_for_x(x)
        # sort by y value
        points = sorted(points, key=lambda p: p[1])
        return points[1 if hi_bit else 0]
    except ValueError:
        return bls12_381_generator.infinity()


def bls12_381_to_bytes(point):
    x, y = point
    if x is None:
        return b''
    as_bytes = bytearray(x.to_bytes(length=BLS12_381_POINT_BYTE_COUNT, byteorder="big", signed=False))
    if y + y > bls12_381_generator.p():
        as_bytes[0] |= 0x80
    return bytes(as_bytes)
