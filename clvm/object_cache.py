from typing import Callable, Dict, Generic, Optional, Tuple, TypeVar

import hashlib

from .CLVMObject import CLVMStorage

T = TypeVar("T")


class ObjectCache(Generic[T]):
    """
    `ObjectCache` provides a way to calculate and cache values for each node
    in a clvm object tree. It can be used to calculate the sha256 tree hash
    for an object and save the hash for all the child objects for building
    usage tables, for example.

    It also allows a function that's defined recursively on a clvm tree to
    have a non-recursive implementation (as it keeps a stack of uncached
    objects locally).
    """

    def __init__(self, f: Callable[["ObjectCache[T]", CLVMStorage], Optional[T]]):
        """
        `f`: Callable[ObjectCache, CLVMObject] -> Union[None, T]

        The function `f` is expected to calculate its T value recursively based
        on the T values for the left and right child for a pair. For an atom, the
        function f must calculate the T value directly.

        If a pair is passed and one of the children does not have its T value cached
        in `ObjectCache` yet, return `None` and f will be called with each child in turn.
        Don't recurse in f; that's part of the point of this function.
        """
        self.f = f
        self.lookup: Dict[int, Tuple[T, CLVMStorage]] = dict()

    def get(self, obj: CLVMStorage) -> T:
        obj_id = id(obj)
        if obj_id not in self.lookup:
            obj_list = [obj]
            while obj_list:
                node = obj_list.pop()
                node_id = id(node)
                if node_id not in self.lookup:
                    v = self.f(self, node)
                    if v is None:
                        if node.pair is None:
                            raise ValueError("f returned None for atom", node)
                        obj_list.append(node)
                        obj_list.append(node.pair[0])
                        obj_list.append(node.pair[1])
                    else:
                        self.lookup[node_id] = (v, node)
        return self.lookup[obj_id][0]

    def contains(self, obj: CLVMStorage) -> bool:
        return id(obj) in self.lookup


def treehash(cache: ObjectCache[bytes], obj: CLVMStorage) -> Optional[bytes]:
    """
    This function can be fed to `ObjectCache` to calculate the sha256 tree
    hash for all objects in a tree.
    """
    if obj.pair:
        left, right = obj.pair

        # ensure both `left` and `right` have cached values
        if cache.contains(left) and cache.contains(right):
            left_hash = cache.get(left)
            right_hash = cache.get(right)
            return hashlib.sha256(b"\2" + left_hash + right_hash).digest()
        return None
    assert obj.atom is not None
    return hashlib.sha256(b"\1" + obj.atom).digest()


def serialized_length(cache: ObjectCache[int], obj: CLVMStorage) -> Optional[int]:
    """
    This function can be fed to `ObjectCache` to calculate the serialized
    length for all objects in a tree.
    """
    if obj.pair:
        left, right = obj.pair

        # ensure both `left` and `right` have cached values
        if cache.contains(left) and cache.contains(right):
            left_length = cache.get(left)
            right_length = cache.get(right)
            return 1 + left_length + right_length
        return None
    assert obj.atom is not None
    lb = len(obj.atom)
    if lb == 0 or (lb == 1 and obj.atom[0] < 128):
        return 1
    if lb < 0x40:
        return 1 + lb
    if lb < 0x2000:
        return 2 + lb
    if lb < 0x100000:
        return 3 + lb
    if lb < 0x8000000:
        return 4 + lb
    if lb < 0x400000000:
        return 5 + lb
    raise ValueError("atom of size %d too long" % lb)
