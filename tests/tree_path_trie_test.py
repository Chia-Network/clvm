import unittest

from clvm.tree_path import TreePath, TOP
from clvm.tree_path_trie import TreePathTrie


class TestTreePathTrie(unittest.TestCase):
    def test_trivial(self) -> None:
        trie = TreePathTrie()
        assert trie.root.value is None
        path2 = TreePath(2)
        trie.insert(path2)

        tns = trie.root.value
        assert tns is not None
        assert tns.min_total_distance == 1
        assert tns.path == path2
        assert tns.next_node.to_left.value is None
        assert tns.next_node.to_right.value is None

        path3 = TreePath(3)
        trie.insert(path3)

        tns = trie.root.value
        assert tns is not None
        assert tns.min_total_distance == 1
        assert tns.path == TOP
        tns_left = tns.next_node.to_left.value
        assert tns_left is not None
        assert tns_left.min_total_distance == 1
        assert tns_left.path == path2
        assert tns_left.next_node.to_left.value is None
        tns_right = tns.next_node.to_right.value
        assert tns_right is not None
        assert tns_right.next_node.to_right.value is None
        assert tns_right.min_total_distance == 1
        assert tns_right.path == path3
        assert tns_right.next_node.to_left.value is None
        assert tns_right.next_node.to_right.value is None

    def test_deeper(self) -> None:
        """
        Here we add paths to 8, then 10, then 22, then 5, then 27, then 31.
        """
        trie = TreePathTrie()
        assert trie.root.value is None

        path8 = TreePath(8)
        trie.insert(path8)

        tns = trie.root.value
        assert tns is not None
        assert tns.min_total_distance == 3
        assert tns.path == path8
        tns_left = tns.next_node.to_left.value
        assert tns_left is None
        tns_right = tns.next_node.to_right.value
        assert tns_right is None

        path10 = TreePath(10)
        trie.insert(path10)
#AI! rename tns_left/tns_right to tns_(node_number) like I've done in later tests
        tns = trie.root.value
        assert tns is not None
        assert tns.min_total_distance == 3
        assert tns.path == 2
        tns_left = tns.next_node.to_left.value
        assert tns_left is not None
        assert tns_left.min_total_distance == 2
        assert tns_left.path == 4
        assert tns_left.next_node.to_left.value is None
        assert tns_left.next_node.to_right.value is None

        tns_right = tns.next_node.to_right.value
        assert tns_right is not None
        assert tns_right.min_total_distance == 2
        assert tns_right.path == 5
        assert tns_right.next_node.to_left.value is None
        assert tns_right.next_node.to_right.value is None

        path22 = TreePath(22)
        trie.insert(path22)

        tns = trie.root.value  # points to 2
        assert tns is not None
        assert tns.min_total_distance == 3
        assert tns.path == 2
        tns_6 = tns.next_node.to_right.value  # right from 2, landing on 6
        assert tns_6 is not None
        assert tns_6.min_total_distance == 2
        assert tns_6.path == 3
        tns_22 = tns_6.next_node.to_right.value  # right from 6, landing on 22
        assert tns_22 is not None
        assert tns_22.min_total_distance == 2
        assert tns_22.path == 5
        assert tns_22.next_node.to_left.value is None
        assert tns_22.next_node.to_right.value is None

        path5 = TreePath(5)
        trie.insert(path5)

        tns = trie.root.value  # points to 1
        assert tns is not None
        assert tns.min_total_distance == 2
        assert tns.path == 1
        tns_l = tns.next_node.to_left.value # left from 1, landing on 2
        assert tns_l is not None
        assert tns_l.min_total_distance == 2
        assert tns_l.path == 2
        # everything else is the same on this side as above
        tns_r = tns.next_node.to_right.value
        assert tns_r is not None
        assert tns_r.min_total_distance == 2
        assert tns_r.path == 5
        assert tns_r.next_node.to_left.value is None
        assert tns_r.next_node.to_right.value is None

