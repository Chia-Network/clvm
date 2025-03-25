from dataclasses import dataclass
from typing import List, Optional

from .tree_path import TreePath, relative_pointer, common_ancestor
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
        for bit in reversed(bin(path)[2:]):  # Iterate through bits of path, skipping "0b1" prefix
            bit_index = int(bit)
            if bit_index == 0:
                if node.to_left is None:
                    node.to_left = TreePath(1)
                node = TrieNode(node.to_left, node.to_right, 0)
            else:
                if node.to_right is None:
                    node.to_right = TreePath(1)
                node = TrieNode(node.to_left, node.to_right, 0)
