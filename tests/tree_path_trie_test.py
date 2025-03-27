import unittest

from clvm.tree_path import TreePath, TOP
from clvm.tree_path_trie import TreePathTrie


class TestTreePathTrie(unittest.TestCase):
    def test_trivial(self) -> None:
        trie = TreePathTrie()
        assert trie.root.value is None
        path2 = TreePath(2)
        trie.insert(path2)

        tn = trie.root.value
        assert tn is not None
        assert tn.min_distance_remaining == 1
        assert tn.path_from_parent == path2
        assert tn.to_left.value is None
        assert tn.to_right.value is None

        path3 = TreePath(3)
        trie.insert(path3)

        tn = trie.root.value
        assert tn is not None
        assert tn.min_distance_remaining == 1
        assert tn.path_from_parent == TOP
        tn_left = tn.to_left.value
        assert tn_left is not None
        assert tn_left.min_distance_remaining == 1
        assert tn_left.path_from_parent == path2
        assert tn_left.to_left.value is None
        tn_right = tn.to_right.value
        assert tn_right is not None
        assert tn_right.to_right.value is None
        assert tn_right.min_distance_remaining == 1
        assert tn_right.path_from_parent == path3
        assert tn_right.to_left.value is None
        assert tn_right.to_right.value is None

    def test_deeper(self) -> None:
        """
        Here we add paths to 8, then 10, then 22, then 5, then 27, then 31.
        """
        trie = TreePathTrie()
        assert trie.root.value is None

        path8 = TreePath(8)
        trie.insert(path8)

        tn = trie.root.value
        assert tn is not None
        assert tn.min_distance_remaining == 3
        assert tn.path_from_parent == path8
        assert tn.to_left.value is None
        assert tn.to_right.value is None

        path10 = TreePath(10)
        trie.insert(path10)
        tn = trie.root.value
        assert tn is not None
        assert tn.min_distance_remaining == 3
        assert tn.path_from_parent == 2
        tn_4 = tn.to_left.value
        assert tn_4 is not None
        assert tn_4.min_distance_remaining == 2
        assert tn_4.path_from_parent == 4
        assert tn_4.to_left.value is None
        assert tn_4.to_right.value is None

        tn_5 = tn.to_right.value
        assert tn_5 is not None
        assert tn_5.min_distance_remaining == 2
        assert tn_5.path_from_parent == 5
        assert tn_5.to_left.value is None
        assert tn_5.to_right.value is None

        path22 = TreePath(22)
        trie.insert(path22)

        tn = trie.root.value  # points to 2
        assert tn is not None
        assert tn.min_distance_remaining == 3
        assert tn.path_from_parent == 2
        assert tn.to_left.value is tn_4
        tn_6 = tn.to_right.value  # right from 2, landing on 6
        assert tn_6 is not None
        assert tn_6.min_distance_remaining == 2
        assert tn_6.path_from_parent == 3
        tn_22 = tn_6.to_right.value  # right from 6, landing on 22
        assert tn_22 is not None
        assert tn_22.min_distance_remaining == 2
        assert tn_22.path_from_parent == 5
        assert tn_22.to_left.value is None
        assert tn_22.to_right.value is None

        path5 = TreePath(5)
        trie.insert(path5)

        tn = trie.root.value  # points to 1
        assert tn is not None
        assert tn.min_distance_remaining == 2
        assert tn.path_from_parent == 1
        tn_2 = tn.to_left.value  # left from 1, landing on 2
        assert tn_2 is not None
        assert tn_2.min_distance_remaining == 3
        assert tn_2.path_from_parent == 2
        # everything else is the same on this side as above
        assert tn_2.to_left.value is tn_4
        assert tn_2.to_right.value is tn_6

        tn_5 = tn.to_right.value
        assert tn_5 is not None
        assert tn_5.min_distance_remaining == 2
        assert tn_5.path_from_parent == 5
        assert tn_5.to_left.value is None
        assert tn_5.to_right.value is None

        path27 = TreePath(27)
        trie.insert(path27)

        tn = trie.root.value  # points to 1
        assert tn is not None
        assert tn.min_distance_remaining == 2
        assert tn.path_from_parent == 1
        assert tn.to_left.value is tn_2

        tn_3 = tn.to_right.value
        assert tn_3 is not None
        assert tn_3.min_distance_remaining == 2
        assert tn_3.path_from_parent == 3
        assert tn_3.to_left.value is not None
        assert tn_3.to_left.value.min_distance_remaining == 1
        assert tn_3.to_left.value.path_from_parent == 2
        assert tn_3.to_left.value.to_left.value is None
        assert tn_3.to_left.value.to_right.value is None

        tn_27 = tn_3.to_right.value
        assert tn_27 is not None
        assert tn_27.min_distance_remaining == 3
        assert tn_27.path_from_parent == 13
        assert tn_27.to_left.value is None
        assert tn_27.to_right.value is None

        path31 = TreePath(31)
        trie.insert(path31)

        tn = trie.root.value  # points to 1
        assert tn is not None
        assert tn.min_distance_remaining == 2
        assert tn.path_from_parent == 1
        assert tn.to_left.value is tn_2
        assert tn.to_right.value is tn_3

        tn_7 = tn_3.to_right.value
        assert tn_7 is not None
        assert tn_7.min_distance_remaining == 3
        assert tn_7.path_from_parent == 3
        tn_27 = tn_7.to_left.value
        assert tn_27 is not None
        assert tn_27.min_distance_remaining == 2
        assert tn_27.path_from_parent == 6
        assert tn_27.to_left.value is None
        assert tn_27.to_right.value is None
        tn_31 = tn_7.to_right.value
        assert tn_31 is not None
        assert tn_31.min_distance_remaining == 2
        assert tn_31.path_from_parent == 7
        assert tn_31.to_left.value is None
        assert tn_31.to_right.value is None
