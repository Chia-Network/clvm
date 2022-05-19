from collections import Counter

import hashlib


def hash_blobs(*blobs):
    s = hashlib.sha256()
    for blob in blobs:
        s.update(blob)
    return s.digest()


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
    """

    def __init__(self):
        """
        Create a new `ReadCacheLookup` object with just the null terminator
        (ie. and empty list of objects).
        """
        self.root_hash = hash_blobs(b"\1")
        self.read_stack = []
        self.count = Counter()
        self.parent_lookup = {}

    def push(self, obj_hash):
        """
        Note that an object with the given hash has just been pushed to
        the read stack, and update the lookups as appropriate.
        """
        # we add two new entries: the new root of the tree, and this object (by id)
        # new_root: (obj_hash, old_root)
        new_root_hash = hash_blobs(b"\2", obj_hash, self.root_hash)

        self.read_stack.append((obj_hash, self.root_hash))

        self.count.update([obj_hash, new_root_hash])

        new_parent_to_old_root = (new_root_hash, 0)
        self.parent_lookup.setdefault(obj_hash, list()).append(new_parent_to_old_root)

        new_parent_to_id = (new_root_hash, 1)
        self.parent_lookup.setdefault(self.root_hash, list()).append(new_parent_to_id)
        self.root_hash = new_root_hash

    def pop(self):
        """
        Note that the top object has just been popped from the read stack.
        Return the 2-tuple of the child hashes.
        """
        item = self.read_stack.pop()
        self.count[item[0]] -= 1
        self.count[self.root_hash] -= 1
        self.root_hash = item[1]
        return item

    def pop2_and_cons(self):
        """
        Note that a "pop-and-cons" operation has just happened. We remove
        two objects, cons them together, and push the cons, updating
        the internal look-ups as necessary.
        """
        # we remove two items: the right side of each left/right pair
        right = self.pop()
        left = self.pop()

        self.count.update([left[0], right[0]])

        new_root_hash = hash_blobs(b"\2", left[0], right[0])

        self.parent_lookup.setdefault(left[0], list()).append((new_root_hash, 0))
        self.parent_lookup.setdefault(right[0], list()).append((new_root_hash, 1))
        self.push(new_root_hash)

    def find_path(self, obj, serialized_length):
        """
        This function looks for a path from the root to a child node with a given hash
        by using the read cache.
        """
        if serialized_length < 3:
            return None

        seen_ids = set()

        max_bytes_for_path_encoding = serialized_length - 2
        # 1 byte for 0xfe, 1 min byte for savings

        max_path_length = max_bytes_for_path_encoding * 8 - 1
        seen_ids.add(obj)

        partial_paths = [(obj, [])]

        while partial_paths:
            new_partial_paths = []
            for (node, path) in partial_paths:
                if node == self.root_hash:
                    path.reverse()
                    return path_to_bytes(path)

                parents = self.parent_lookup.get(node)

                if parents:
                    for (parent, direction) in parents:
                        if self.count[parent] > 0 and parent not in seen_ids:
                            new_path = list(path)
                            new_path.append(direction)
                            if len(new_path) > max_path_length:
                                return None
                            new_partial_paths.append((parent, new_path))
                        seen_ids.add(parent)
            partial_paths = new_partial_paths
        return None


def path_to_bytes(path):
    """
    Convert a list of 0/1 values to a path expected by clvm.
    """
    byte_count = (len(path) + 1 + 7) >> 3
    v = bytearray(byte_count)
    index = byte_count - 1
    mask = 1
    for p in path:
        if p:
            v[index] |= mask
        if mask == 0x80:
            index -= 1
            mask = 1
        else:
            mask <<= 1
    v[index] |= mask
    return v
