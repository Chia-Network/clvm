from dataclasses import dataclass
from typing import Optional

from .tree_path import TreePath


@dataclass
class TrieNode:
    closest_leaf_distance: int  # this is from the *parent*
    path_from_parent: TreePath
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
            if is_prefix(trie_node.path_from_parent, path):
                # this is a proper prefix. Let's go down the tree to the next branch
                trie_node.closest_leaf_distance = min(
                    trie_node.closest_leaf_distance, path_size
                )
                trie_path_size = len(bin(trie_node.path_from_parent)[3:])
                path = path.remaining_steps(trie_path_size)
                path_size -= trie_path_size
                assert int(path) > 1, "path is not a proper prefix"
                branch = trie_node.to_right if path & 1 else trie_node.to_left
                continue

            # this is not a proper prefix
            # we need to split the node
            # we create a 1 and a 2. The 1 has the same root as the original node and
            # the 2 has the same destination as the original node

            prefix_path = trie_node.path_from_parent.common_ancestor(path)
            prefix_path_size = len(bin(prefix_path)[3:])

            new_branch_value = split_branch(trie_node, prefix_path_size)
            branch.value = new_branch_value

    def find_shortest_relative_pointer(
        self, source_node_path: TreePath, max_path_length: int
    ) -> Optional[TreePath]:
        # set up a list of things `to_consider`
        # each thing has: a potential branch; a "right count" of 1 bits to get to the common branch of
        # the potential branch and the target branch; and a partial path to get from the common branch to the
        # potential branch.
        #
        # We start at the root. Then we follow the target path, salting away into the `to_consider` list
        # whenever the branch also goes to the right when we're going left. (The other case does not
        # matter due to the order we're serializing)

        branch = self.root

        best_path_trie_node: Optional[TrieNode] = None
        best_path_right_count: int = 0

        source_node_path_right_count = right_count_for_path(source_node_path)

        # step 1: follow the trie down the target path as far as
        # we can. Once it branches, create a new `Branch`
        # If we ever go right at a `Branch` that also has a
        # left, add it to the `to_consider` list (and update max_path_length).

        while branch.value is not None:
            trie_node = branch.value
            prefix_path = trie_node.path_from_parent.common_ancestor(source_node_path)
            prefix_path_size = len(bin(prefix_path)[3:])
            if prefix_path == trie_node.path_from_parent:
                for _ in range(prefix_path_size):
                    if source_node_path & 1:
                        source_node_path_right_count -= 1
                    source_node_path = source_node_path.remaining_steps(1)

                # do we need to consider the left branch as a relative pointer?
                if trie_node.to_left.value is not None and source_node_path & 1:
                    # we need to consider the left branch
                    left_path_length = (
                        trie_node.to_left.value.closest_leaf_distance
                        + source_node_path_right_count
                    )
                    if left_path_length < max_path_length:
                        max_path_length = left_path_length
                        best_path_trie_node = trie_node.to_left.value
                        best_path_right_count = source_node_path_right_count
                # now continue following the source node path
                branch = (
                    trie_node.to_right if source_node_path & 1 else trie_node.to_left
                )
            else:
                # we have to split this branch
                temp_trie_node = split_branch(trie_node, prefix_path_size)
                branch = Branch(temp_trie_node)

        # okay, we're done. Our best path can be found by tracing down
        # `best_path_trie_node`. Let's calculate it

        if best_path_trie_node is None:
            return None

        best_path_str = "1" * (best_path_right_count - 1)

        better_branch = best_path_trie_node
        while True:
            best_path_str = bin(better_branch.path_from_parent)[3:] + best_path_str
            # which is better, left or right?
            left = better_branch.to_left.value
            right = better_branch.to_right.value
            if left is None and right is None:
                break
            if right is None or (
                left is not None
                and left.closest_leaf_distance < right.closest_leaf_distance
            ):
                assert left is not None
                better_branch = left
            else:
                better_branch = right
            assert better_branch is not None

        best_path_str = "1" + best_path_str

        return TreePath(int(best_path_str, 2))


def right_count_for_path(path: TreePath) -> int:
    """
    Count the number of "right" branches in a path.
    """
    # subtract 1 for the sentinel
    return bin(path).count("1") - 1


def split_branch(trie_node: TrieNode, prefix_path_size: int) -> TrieNode:
    new_path_1, new_path_2 = trie_node.path_from_parent.split(prefix_path_size)

    new_total_distance_2 = trie_node.closest_leaf_distance - prefix_path_size

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
        trie_node.closest_leaf_distance, new_path_1, new_left_branch, new_right_branch
    )
    return new_trie_node_1
