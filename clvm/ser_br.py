from typing import Dict, Iterator, List, Optional, Tuple

from .CLVMObject import CLVMStorage

from .casts import limbs_for_int
from .object_cache import ObjectCache, treehash, serialized_length
from .serialize import atom_to_byte_iterator, BACK_REFERENCE, CONS_BOX_MARKER


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


def all_nodes(obj: CLVMStorage) -> Iterator[Tuple[CLVMStorage, TreePath]]:
    to_yield: List[Tuple[CLVMStorage, TreePath]] = [(obj, TOP)]
    while to_yield:
        obj, path = to_yield.pop()
        yield obj, path
        if obj.pair is not None:
            to_yield.append((obj.pair[1], path.right()))
            to_yield.append((obj.pair[0], path.left()))


def sexp_to_byte_iterator_with_backrefs(obj: CLVMStorage) -> Iterator[bytes]:
    thc = ObjectCache(treehash)
    slc = ObjectCache(serialized_length)

    paths_for_hash: Dict[bytes, List[TreePath]] = {}

    for node, path in all_nodes(obj):
        node_tree_hash = thc.get(node)
        paths_for_hash.setdefault(node_tree_hash, []).append(path)

    # in `read_op_stack`:
    #  "P" = "push"
    #  "C" = "pop two objects, create and push a new cons with them"

    read_op_stack = ["P"]

    write_stack: List[Tuple[CLVMStorage, TreePath]] = [(obj, TOP)]

    while write_stack:
        node_to_write, tree_path = write_stack.pop()
        op = read_op_stack.pop()
        assert op == "P"

        node_serialized_length = slc.get(node_to_write)

        node_tree_hash = thc.get(node_to_write)
        possible_paths = paths_for_hash.get(node_tree_hash, [])
        maybe_path = None
        if len(possible_paths) > 1 and node_serialized_length > 3:
            maybe_path = find_short_path(tree_path, possible_paths, node_serialized_length)
        if maybe_path is not None:
            yield bytes([BACK_REFERENCE])
            yield from atom_to_byte_iterator(bytes(maybe_path))
        elif node_to_write.pair:
            left, right = node_to_write.pair
            yield bytes([CONS_BOX_MARKER])
            write_stack.append((right, tree_path.right()))
            write_stack.append((left, tree_path.left()))
            read_op_stack.append("C")
            read_op_stack.append("P")
            read_op_stack.append("P")
        else:
            atom = node_to_write.atom
            assert atom is not None
            yield from atom_to_byte_iterator(atom)

        while read_op_stack[-1:] == ["C"]:
            read_op_stack.pop()


def are_paths_in_order(path1: int | TreePath, path2: int | TreePath) -> bool:
    """
    Returns True if `path1` would be processed before `path2` when
    serializing the tree.
    """
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


def find_short_path(
    tree_path: TreePath,
    possible_paths: List[TreePath],
    node_serialized_length: int,
) -> Optional[TreePath]:
    if possible_paths is None or len(possible_paths) == 1:
        return None
    best_size: int = node_serialized_length
    best_path: Optional[TreePath] = None
    for path in possible_paths:
        if are_paths_in_order(tree_path, path):
            break
        # the paths are in order
        relative_path = relative_pointer(path, tree_path)
        size = limbs_for_int(relative_path) + 1
        if best_size is None or size < best_size:
            best_size = size
            best_path = relative_path
    return best_path


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

    if not are_paths_in_order(n, m):
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
