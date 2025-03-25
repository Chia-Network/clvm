from typing import Union

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

    def common_ancestor(self, other: Union[int, "TreePath"]) -> "TreePath":
        """
        Returns the common ancestor of `path1` and `path2`.
        """
        path1 = self
        path2 = other
        if path1 == path2:
            return TreePath(path1)
        mask = 1
        while (path1 & mask) == (path2 & mask):
            mask <<= 1
            mask |= 1
        common_path = path1 & mask | ((mask + 1) >> 1)
        return TreePath(common_path)

    def __lt__(self, other: Union[int, "TreePath"]) -> bool:
        """
        Returns True if `self` would be processed before `other` when
        serializing the tree.
        """
        path1 = self
        path2 = other
        while path1 > 1 and path2 > 1:
            d1 = path1 & 1
            d2 = path2 & 1
            if d2 == 0 and d1 == 1:
                return False
            if d2 == 1 and d1 == 0:
                return True
            path1 >>= 1
            path2 >>= 1
        # we are at the case where one path is a prefix of the other
        # the longer path is processed first
        return path1 >= path2

    def __bytes__(self) -> bytes:
        if self == 0:
            return b""
        byte_count = (self.bit_length() + 7) >> 3
        r = self.to_bytes(byte_count, "big", signed=False)
        # make sure the string returned is minimal
        # ie. no leading 00 bytes that are unnecessary
        assert r == b"" or r[0] != 0
        return r


TOP = TreePath(1)

# AI! make this a method on TreePath and implement the freestanding function in terms of the new method.
def relative_pointer(n: int | TreePath, m: int | TreePath) -> TreePath:
    """
    Given two absolute path numbers n and m (with n to the left of m),
    compute a pointer (encoded as a path number) that, when followed from
    the top of the stack state at m, reaches n.

    The absolute paths are encoded in binary with an implicit leading 1;
    when that is stripped, the remaining bits (when read in reverse order)
    indicate the directions (0 for left, 1 for right) in the order in which
    branches are taken (LSB is the first branch). We compute the relative
    pointer by removing the common prefix (of reversed bits) and re-encoding
    the remainder.

    The key observation is that we remove the common prefix.
    Then what's left of m, we can remove all the `0` bits and the
    sentinel `1` bit. What's left is the path from the root to the
    top of the common part of the stack tree.

    Then we simply follow the path from here to the remaining part
    of n to get to where n currently is in the stack.
    """

    def get_reversed_path(x: int) -> list[int]:
        # Convert x to binary, remove the leading "1" (which represents the root),
        # and then reverse the remaining bits so that the LSB becomes the first branch.
        b = bin(x)[3:]  # e.g., for x == 6 ('0b110'), b becomes "10"
        return [int(ch) for ch in b[::-1]]

    if not TreePath(n) < TreePath(m):
        raise ValueError("n must be to the left of m")

    path_n = get_reversed_path(n)
    path_m = get_reversed_path(m)

    # Find the length of the common prefix.
    i = 0
    while i < len(path_n) and i < len(path_m) and path_n[i] == path_m[i]:
        i += 1
    # The remaining bits of n (after the common prefix) form the relative path.
    rel_bits = [_ for _ in path_m[i + 1 :] if _ == 1]
    rel_bits.extend(path_n[i:])

    # Re-encode the relative pointer using the same scheme.
    # We start with a 1 (which is the root in our pointer tree) and then append
    # the bits from rel_bits (processing from most significant to least significant).
    p = 1
    for bit in reversed(rel_bits):
        p = (p << 1) | bit
    return TreePath(p)


def common_ancestor(n: int | TreePath, m: int | TreePath) -> TreePath:
    """
    Returns the common ancestor of `n` and `m`.
    """
    return TreePath(n).common_ancestor(m)
