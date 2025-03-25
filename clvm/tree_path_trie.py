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

    def insert(self, path: TreePath) -> None: # AI! get this working
        node = self.root
        # node.min_size = min(node.min_size or serialized_length, serialized_length)
        for bit in reversed(
            bin(path)[3:]
        ):  # Iterate through bits of path, skipping "0b1" prefix
            bit_index = int(bit)
            # if node.children[bit_index] is None:
            #    next_path = node.path.left() if bit_index == 0 else node.path.right()
            #    node.children[bit_index] = TrieNode(next_path)
            # next_node = node.children[bit_index]
            # if next_node is not None:
            #    node = next_node
            #    node.min_size = min(
            #        node.min_size or serialized_length, serialized_length
            #    )
