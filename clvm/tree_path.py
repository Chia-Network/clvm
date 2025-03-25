from .casts import limbs_for_int


class TreePath(int):
    def __new__(self, value: int) -> "TreePath":
        return int.__new__(TreePath, value)

    def extend(self, is_right: bool) -> "TreePath":
        if is_right:
            new_high_bit = 1 << (self.bit_length())
            return TreePath(self | new_high_bit)
        flip_bit = (1 << (self.bit_length() - 1)) * 3
        return TreePath(self ^ flip_bit)

    def left(self) -> "TreePath":
        return self.extend(is_right=False)

    def right(self) -> "TreePath":
        return self.extend(is_right=True)

    def size_in_bytes(self) -> int:
        return limbs_for_int(self)

    def path(self, fr_str: str) -> "TreePath":
        t = self
        for c in fr_str:
            if c in "fl":
                t = t.left()
            elif c == "r":
                t = t.right()
            else:
                raise ValueError(f"invalid path character {c}")
        return t

    def __bytes__(self) -> bytes:
        if self == 0:
            return b""
        byte_count = (self.bit_length() + 7) >> 3
        r = self.to_bytes(byte_count, "big", signed=False)
        # make sure the string returned is minimal
        # ie. no leading 00 bytes that are unnecessary
        while len(r) > 1 and r[0] == 0:
            breakpoint()
            r = r[1:]
        return r


TOP = TreePath(1)
