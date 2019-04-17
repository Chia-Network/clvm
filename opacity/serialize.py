
def encode_size(f, size, step_size, base_byte_int):
    step_count, remainder = divmod(size, step_size)
    if step_count > 0:
        f.write(b'\x60')
        step_count -= 1
        while step_count > 0:
            step_count, r = divmod(step_count, 32)
            f.write(bytes([r]))
    f.write(bytes([base_byte_int+remainder]))


def sexp_to_stream(v, f):
    if v.is_bytes():
        blob = v.as_bytes()
        size = len(blob)
        if size == 0:
            f.write(b'\0')
            return
        if size == 1:
            v1 = v.as_int()
            if v1 and 0 < v1 <= 31:
                f.write(bytes([v1 & 0x3f]))
                return
        encode_size(f, size, 160, 0x60)
        f.write(blob)
        return

    if v.listp():
        encode_size(f, len(v), 32, 0x20)
        for _ in v:
            sexp_to_stream(_, f)
        return

    if v.is_var():
        encode_size(f, v.var_index(), 32, 0x40)
        return

    assert 0


def decode_size(f):
    steps = 0
    b = f.read(1)
    if len(b) == 0:
        raise ValueError("unexpected end of stream")
    v = b[0]
    if v == 0x60:
        steps = 1
        shift_count = 0
        while True:
            b = f.read(1)
            if len(b) == 0:
                raise ValueError("unexpected end of stream")
            v = b[0]
            if v >= 0x20:
                break
            steps += (v << shift_count)
            shift_count += 5

    return steps, v


def sexp_from_stream(f, class_):
    steps, v = decode_size(f)
    if v == 0:
        return class_(b'')

    if v < 0x20:
        return class_(bytes([v]))

    if v < 0x40:
        size = v - 0x20 + steps * 0x20
        items = [sexp_from_stream(f, class_) for _ in range(size)]
        return class_(items)

    if v < 0x60:
        index = v - 0x40 + steps * 0x20
        return class_.from_var_index(index)

    size = v - 0x60 + steps * 160
    blob = f.read(size)
    if len(blob) < size:
        raise ValueError("unexpected end of stream")
    return class_(blob)
