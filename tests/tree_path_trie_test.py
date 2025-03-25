import unittest

from clvm.tree_path import TreePath
from clvm.tree_path_trie import TreePathTrie


class TestTreePathTrie(unittest.TestCase):
    def test_insert(self) -> None:
        trie = TreePathTrie()
        path1 = TreePath(5)
        path2 = TreePath(6)
        trie.insert(path1)
        trie.insert(path2)

    def test_find_shortest_path(self) -> None:
        trie = TreePathTrie()
        path1 = TreePath(5)
        path2 = TreePath(6)
        trie.insert(path1)
        trie.insert(path2)
        shortest_path = trie.find_shortest_path(TreePath(5), 10)
        self.assertEqual(shortest_path, None)
