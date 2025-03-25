import unittest

from clvm.tree_path import TreePath
from clvm.tree_path_trie import TreePathTrie


class TestTreePathTrie(unittest.TestCase):
    def test_trivial(self) -> None:
        trie = TreePathTrie()
        path2 = TreePath(2)
        trie.insert(path2)
        assert trie.root.to_left == path2
        assert trie.root.to_right is None
        path3 = TreePath(3)
        trie.insert(path3)
        assert trie.root.to_left == path2
        assert trie.root.to_right == path3

    def test_deeper(self) -> None:
        trie = TreePathTrie()
        path18 = TreePath(0b10010)
        trie.insert(path18)
        assert trie.root.to_left == path18
        assert trie.root.to_right is None
        path13 = TreePath(0b1101)
        trie.insert(path13)
        assert trie.root.to_left == path18
        assert trie.root.to_right == path13
        path11 = TreePath(0b1011)
        trie.insert(path11)
        assert trie.root.to_left is not None
        assert trie.root.to_right is not None
