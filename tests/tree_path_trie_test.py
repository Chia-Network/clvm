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
        assert tns.to_left.value is None
        assert tns.to_right.value is None

        path3 = TreePath(3)
        trie.insert(path3)

        tns = trie.root.value
        assert tns is not None
        assert tns.min_total_distance == 1
        assert tns.path == TOP
        tns_left = tns.to_left.value
        assert tns_left is not None
        assert tns_left.min_total_distance == 1
        assert tns_left.path == path2
        assert tns_left.to_left.value is None
        tns_right = tns.to_right.value
        assert tns_right is not None
        assert tns_right.to_right.value is None
        assert tns_right.min_total_distance == 1
        assert tns_right.path == path3
        assert tns_right.to_left.value is None
        assert tns_right.to_right.value is None

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
        assert tns.to_left.value is None
        assert tns.to_right.value is None

        path10 = TreePath(10)
        trie.insert(path10)
        tns = trie.root.value
        assert tns is not None
        assert tns.min_total_distance == 3
        assert tns.path == 2
        tns_4 = tns.to_left.value
        assert tns_4 is not None
        assert tns_4.min_total_distance == 2
        assert tns_4.path == 4
        assert tns_4.to_left.value is None
        assert tns_4.to_right.value is None

        tns_5 = tns.to_right.value
        assert tns_5 is not None
        assert tns_5.min_total_distance == 2
        assert tns_5.path == 5
        assert tns_5.to_left.value is None
        assert tns_5.to_right.value is None

        path22 = TreePath(22)
        trie.insert(path22)

        tns = trie.root.value  # points to 2
        assert tns is not None
        assert tns.min_total_distance == 3
        assert tns.path == 2
        assert tns.to_left.value is tns_4
        tns_6 = tns.to_right.value  # right from 2, landing on 6
        assert tns_6 is not None
        assert tns_6.min_total_distance == 2
        assert tns_6.path == 3
        tns_22 = tns_6.to_right.value  # right from 6, landing on 22
        assert tns_22 is not None
        assert tns_22.min_total_distance == 2
        assert tns_22.path == 5
        assert tns_22.to_left.value is None
        assert tns_22.to_right.value is None

        path5 = TreePath(5)
        trie.insert(path5)

        tns = trie.root.value  # points to 1
        assert tns is not None
        assert tns.min_total_distance == 2
        assert tns.path == 1
        tns_2 = tns.to_left.value  # left from 1, landing on 2
        assert tns_2 is not None
        assert tns_2.min_total_distance == 2
        assert tns_2.path == 2
        # everything else is the same on this side as above
        assert tns_2.to_left.value is tns_4
        assert tns_2.to_right.value is tns_6

        tns_5 = tns.to_right.value
        assert tns_5 is not None
        assert tns_5.min_total_distance == 2
        assert tns_5.path == 5
        assert tns_5.to_left.value is None
        assert tns_5.to_right.value is None

        path27 = TreePath(27)
        trie.insert(path27)

        tns = trie.root.value  # points to 1
        assert tns is not None
        assert tns.min_total_distance == 2
        assert tns.path == 1
        assert tns.to_left.value is tns_2

        tns_3 = tns.to_right.value
        assert tns_3 is not None
        # assert tns_3.min_total_distance == 1
        assert tns_3.path == 3
        # assert tns_3.to_left.value is tns_5
        tns_27 = tns_3.to_right.value
        assert tns_27 is not None
        assert tns_27.min_total_distance == 3
        assert tns_27.path == 13
        assert tns_27.to_left.value is None
        assert tns_27.to_right.value is None
