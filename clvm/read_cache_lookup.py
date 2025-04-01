from collections import Counter
from typing import Dict, Optional, List, Set, Tuple

import hashlib


LEFT = 0
RIGHT = 1


class ReadCacheLookup:
    """
    When deserializing a clvm object, a stack of deserialized child objects
    is created, which can be used with back-references. A `ReadCacheLookup` keeps
    track of the state of this stack and all child objects under each root
    node in the stack so that we can quickly determine if a relevant
    back-reference is available.

    In other words, if we've already serialized an object with tree hash T,
    and we encounter another object with that tree hash, we don't re-serialize
    it, but rather include a back-reference to it. This data structure lets
    us quickly determine which back-reference has the shortest path.

    Note that there is a counter. This is because the stack contains some
    child objects that are transient, and no longer appear in the stack
    at later times in the parsing. We don't want to waste time looking for
    these objects that no longer exist, so we reference-count them.

    All hashes correspond to sha256 tree hashes.
    """

    def __init__(self) -> None:
        """
        Create a new `ReadCacheLookup` object with just the null terminator
        (ie. an empty list of objects).
        """
        self.root_hash = hashlib.sha256(b"\1").digest()
        self.read_stack: List[Tuple[bytes, bytes]] = []
        self.count: Counter[bytes] = Counter()
        self.parent_paths_for_child: Dict[bytes, List[Tuple[bytes, int]]] = {}

    def push(self, obj_hash: bytes) -> None:
        """
        This function is used to note that an object with the given hash has just
        been pushed to the read stack, and update the lookups as appropriate.
        """
        # we add two new entries: the new root of the tree, and this object (by id)
        # new_root: (obj_hash, old_root)
        new_root_hash = hashlib.sha256(b"\2" + obj_hash + self.root_hash).digest()

        self.read_stack.append((obj_hash, self.root_hash))

        self.count.update([obj_hash, new_root_hash])

        new_parent_to_old_root = (new_root_hash, LEFT)
        self.parent_paths_for_child.setdefault(obj_hash, list()).append(
            new_parent_to_old_root
        )

        new_parent_to_id = (new_root_hash, RIGHT)
        self.parent_paths_for_child.setdefault(self.root_hash, list()).append(
            new_parent_to_id
        )
        self.root_hash = new_root_hash

    def pop(self) -> Tuple[bytes, bytes]:
        """
        This function is used to note that the top object has just been popped
        from the read stack. Return the 2-tuple of the child hashes.
        """
        item = self.read_stack.pop()
        self.count[item[0]] -= 1
        self.count[self.root_hash] -= 1
        self.root_hash = item[1]
        return item

    def pop2_and_cons(self) -> None:
        """
        This function is used to note that a "pop-and-cons" operation has just
        happened. We remove two objects, cons them together, and push the cons,
        updating the internal look-ups as necessary.
        """
        # we remove two items: the right side of each left/right pair
        right = self.pop()
        left = self.pop()

        self.count.update([left[0], right[0]])

        new_root_hash = hashlib.sha256(b"\2" + left[0] + right[0]).digest()

        self.parent_paths_for_child.setdefault(left[0], list()).append(
            (new_root_hash, LEFT)
        )
        self.parent_paths_for_child.setdefault(right[0], list()).append(
            (new_root_hash, RIGHT)
        )
        self.push(new_root_hash)

    def find_paths(self, obj_hash: bytes, serialized_length: int) -> Set[bytes]:
        """
        This function looks for a path from the root to a child node with a given hash
        by using the read cache.
        """
        valid_paths: Set[bytes] = set()
        if serialized_length < 3:
            return valid_paths

        seen_ids: Set[bytes] = set()

        max_bytes_for_path_encoding = serialized_length - 2
        # 1 byte for 0xfe, 1 min byte for savings

        max_path_length = max_bytes_for_path_encoding * 8 - 1
        seen_ids.add(obj_hash)

        partial_paths: List[Tuple[bytes, List[int]]] = [(obj_hash, [])]

        while partial_paths:
            new_seen_ids = set(seen_ids)
            new_partial_paths = []
            for node, path in partial_paths:
                if node == self.root_hash:
                    valid_paths.add(reversed_path_to_bytes(path))
                    continue

                parent_paths = self.parent_paths_for_child.get(node)

                if parent_paths:
                    for parent, direction in parent_paths:
                        if self.count[parent] > 0 and parent not in seen_ids:
                            new_path = list(path)
                            new_path.append(direction)
                            if len(new_path) > max_path_length:
                                return set()
                            new_partial_paths.append((parent, new_path))
                        new_seen_ids.add(parent)
            partial_paths = new_partial_paths
            if valid_paths:
                return valid_paths
            seen_ids = set(new_seen_ids)
        return valid_paths

    def find_path(self, obj_hash: bytes, serialized_length: int) -> Optional[bytes]:
        r = self.find_paths(obj_hash, serialized_length)
        return min(r) if len(r) > 0 else None


def reversed_path_to_bytes(path: List[int]) -> bytes:
    """
    Convert a list of 0/1 (for left/right) values to a path expected by clvm.

    Reverse the list; convert to a binary number; prepend a 1; break into bytes.

    [] => bytes([0b1])
    [0] => bytes([0b10])
    [1] => bytes([0b11])
    [0, 0] => bytes([0b100])
    [0, 1] => bytes([0b101])
    [1, 0] => bytes([0b110])
    [1, 1] => bytes([0b111])
    [0, 0, 1] => bytes([0b1001])
    [1, 1, 1, 1, 0, 0, 0, 0, 1] => bytes([0b11, 0b11100001])
    """

    byte_count = (len(path) + 1 + 7) >> 3
    v = bytearray(byte_count)
    index = byte_count - 1
    mask = 1
    for p in reversed(path):
        if p:
            v[index] |= mask
        if mask == 0x80:
            index -= 1
            mask = 1
        else:
            mask <<= 1
    v[index] |= mask
    return bytes(v)
