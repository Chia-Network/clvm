from dataclasses import dataclass
from typing import List, Optional

from .tree_path import TreePath, relative_pointer, are_paths_in_order
from .casts import limbs_for_int


@dataclass
class TrieNode:
    to_left: Optional[TreePath]
    to_right: Optional[TreePath]
    min_distance: int


@dataclass
class TreePathTrie:
    root: TrieNode

    def __init__(self) -> None:
        self.root = TrieNode(None, None, 0)  # TOP

    def insert(self, path: TreePath) -> None:
        node = self.root
        for bit in reversed(bin(path)[3:]):  # Iterate through bits of path, skipping "0b1" prefix
            bit_index = int(bit)
            if bit_index == 0:
                if node.to_left is None:
                    node.to_left = TreePath(int(bin(path)[2:], 2)) # This might be wrong
                node = TrieNode(node.to_left, None, 0)
            else:
                if node.to_right is None:
                    node.to_right = TreePath(int(bin(path)[2:], 2)) # This might be wrong
                node = TrieNode(None, node.to_right, 0)
