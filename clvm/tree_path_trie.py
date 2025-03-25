from typing import List, Optional

from .tree_path import TreePath
from .ser_br import relative_pointer, are_paths_in_order, limbs_for_int


class TrieNode:
    def __init__(self, path: TreePath, min_size: Optional[int] = None) -> None:
        self.path = path
        self.min_size = min_size
        self.children: List[Optional["TrieNode"]] = [
            None,
            None,
        ]  # [left (0), right (1)]


class TreePathTrie:
    def __init__(self) -> None:
        self.root = TrieNode(TreePath(1))  # TOP

    def insert(self, path: TreePath, serialized_length: int) -> None:
        node = self.root
        node.min_size = min(node.min_size or serialized_length, serialized_length)
        for bit in reversed(
            bin(path)[3:]
        ):  # Iterate through bits of path, skipping "0b1" prefix
            bit_index = int(bit)
            if node.children[bit_index] is None:
                next_path = node.path.left() if bit_index == 0 else node.path.right()
                node.children[bit_index] = TrieNode(next_path)
            node = node.children[bit_index]
            node.min_size = min(node.min_size or serialized_length, serialized_length)

    def find_shortest_path(
        self, tree_path: TreePath, serialized_length: int
    ) -> Optional[bytes]:
        best_path: Optional[bytes] = None
        best_size: Optional[int] = serialized_length
        node: Optional[TrieNode] = self.root

        def traverse(node: Optional["TrieNode"]) -> None:
            nonlocal best_path, best_size
            if node is None or (
                node.min_size is not None
                and best_size is not None
                and (node.min_size <= best_size)
            ):
                return

            relative = relative_pointer(node.path, tree_path)
            size = limbs_for_int(relative) + 1

            if size < (best_size or float("inf")) and are_paths_in_order(
                node.path, tree_path
            ):
                best_size = size
                best_path = bytes(relative)

            traverse(node.children[0])  # left
            traverse(node.children[1])  # right

        traverse(node)
        return best_path
