from dataclasses import dataclass
from typing import Optional

from .tree_path import TreePath


@dataclass
class TrieNode:
    min_total_distance: int
    path: TreePath
    to_left: "Branch"
    to_right: "Branch"


@dataclass
class Branch:
    value: Optional[TrieNode]


def is_prefix(prefix: TreePath, path: TreePath) -> bool:
    p1 = int(prefix)
    p2 = int(path)
    while True:
        if p1 == 1:
            return True
        if p1 & 1 != p2 & 1:
            return False
        p1 >>= 1
        p2 >>= 1


def path_length(path: TreePath) -> int:
    return len(bin(path)[3:])


@dataclass
class TreePathTrie:
    root: Branch

    def __init__(self) -> None:
        self.root = Branch(None)

    def insert(self, path: TreePath) -> None:
        branch: Branch = self.root
        path_size = path_length(path)
        while True:
            trie_node = branch.value
            if trie_node is None:
                total_distance = len(bin(path)[3:])
                left_branch = Branch(None)
                right_branch = Branch(None)
                branch.value = TrieNode(total_distance, path, left_branch, right_branch)
                return
            trie_node.min_total_distance = min(trie_node.min_total_distance, path_size)
            if is_prefix(trie_node.path, path):
                # this is a proper prefix. Let's go down the tree to the next branch
                trie_path_size = len(bin(trie_node.path)[3:])
                path = path.remaining_steps(trie_path_size)
                path_size -= trie_path_size
                assert int(path) > 0, "path is not a proper prefix"
                branch = trie_node.to_right if path & 1 else trie_node.to_left
                continue

            # this is not a proper prefix
            # we need to split the node
            # we create a 1 and a 2. The 1 has the same root as the original node and
            # the 2 has the same destination as the original node

            prefix_path = trie_node.path.common_ancestor(path)
            prefix_path_size = len(bin(prefix_path)[3:])

            new_branch_value = split_branch(trie_node, prefix_path_size)
            branch.value = new_branch_value


def split_branch(trie_node: TrieNode, prefix_path_size: int) -> TrieNode:
    new_path_1, new_path_2 = trie_node.path.split(prefix_path_size)

    new_total_distance_2 = trie_node.min_total_distance - prefix_path_size

    new_trie_node_2 = TrieNode(
        new_total_distance_2,
        new_path_2,
        trie_node.to_left,
        trie_node.to_right,
    )

    new_left_branch = Branch(new_trie_node_2)
    new_right_branch = Branch(None)
    # should we swap left & right?
    if new_path_2 & 1:
        new_left_branch, new_right_branch = new_right_branch, new_left_branch
    new_trie_node_1 = TrieNode(
        trie_node.min_total_distance, new_path_1, new_left_branch, new_right_branch
    )
    return new_trie_node_1
