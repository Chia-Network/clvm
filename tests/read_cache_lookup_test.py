import unittest

from clvm import to_sexp_f
from clvm.read_cache_lookup import ReadCacheLookup
from clvm.object_cache import ObjectCache, treehash


class ReadCacheLookupTest(unittest.TestCase):
    def test_various(self) -> None:
        rcl = ReadCacheLookup()
        treehasher = ObjectCache(treehash)

        # rcl = ()
        nil = to_sexp_f(b"")
        nil_hash = treehasher.get(nil)
        self.assertEqual(rcl.root_hash, nil_hash)

        foo = to_sexp_f(b"foo")
        foo_hash = treehasher.get(foo)
        rcl.push(foo_hash)

        # rcl = (foo . 0)

        current_stack = to_sexp_f([foo])
        current_stack_hash = treehasher.get(current_stack)

        self.assertEqual(rcl.root_hash, current_stack_hash)
        self.assertEqual(rcl.find_path(foo_hash, serialized_length=20), bytes([2]))
        self.assertEqual(rcl.find_path(nil_hash, serialized_length=20), bytes([3]))
        self.assertEqual(
            rcl.find_path(current_stack_hash, serialized_length=20), bytes([1])
        )

        bar = to_sexp_f(b"bar")
        bar_hash = treehasher.get(bar)
        rcl.push(bar_hash)

        # rcl = (bar foo)

        current_stack = to_sexp_f([bar, foo])
        current_stack_hash = treehasher.get(current_stack)
        foo_list_hash = treehasher.get(to_sexp_f([b"foo"]))
        self.assertEqual(rcl.root_hash, current_stack_hash)
        self.assertEqual(rcl.find_path(bar_hash, serialized_length=20), bytes([2]))
        self.assertEqual(rcl.find_path(foo_list_hash, serialized_length=20), bytes([3]))
        self.assertEqual(rcl.find_path(foo_hash, serialized_length=20), bytes([5]))
        self.assertEqual(rcl.find_path(nil_hash, serialized_length=20), bytes([7]))
        self.assertEqual(
            rcl.find_path(current_stack_hash, serialized_length=20), bytes([1])
        )
        self.assertEqual(rcl.count[foo_list_hash], 1)

        rcl.pop2_and_cons()
        # rcl = ((foo . bar) . 0)

        current_stack = to_sexp_f([(foo, bar)])
        current_stack_hash = treehasher.get(current_stack)
        self.assertEqual(rcl.root_hash, current_stack_hash)

        # we no longer have `(foo . 0)` in the read stack
        # check that its count is zero
        self.assertEqual(rcl.count[foo_list_hash], 0)

        self.assertEqual(rcl.find_path(bar_hash, serialized_length=20), bytes([6]))
        self.assertEqual(rcl.find_path(foo_list_hash, serialized_length=20), None)
        self.assertEqual(rcl.find_path(foo_hash, serialized_length=20), bytes([4]))
        self.assertEqual(rcl.find_path(nil_hash, serialized_length=20), bytes([3]))
        self.assertEqual(
            rcl.find_path(current_stack_hash, serialized_length=20), bytes([1])
        )

        rcl.push(foo_hash)
        rcl.push(foo_hash)
        rcl.pop2_and_cons()

        # rcl = ((foo . foo) (foo . bar))

        current_stack = to_sexp_f([(foo, foo), (foo, bar)])
        current_stack_hash = treehasher.get(current_stack)
        self.assertEqual(rcl.root_hash, current_stack_hash)
        self.assertEqual(rcl.find_path(bar_hash, serialized_length=20), bytes([13]))
        self.assertEqual(rcl.find_path(foo_list_hash, serialized_length=20), None)
        self.assertEqual(rcl.find_path(foo_hash, serialized_length=20), bytes([4]))
        self.assertEqual(rcl.find_path(nil_hash, serialized_length=20), bytes([7]))

        # find BOTH minimal paths to `foo`
        self.assertEqual(
            rcl.find_paths(foo_hash, serialized_length=20),
            set([bytes([4]), bytes([6])]),
        )

        rcl = ReadCacheLookup()
        rcl.push(foo_hash)
        rcl.push(foo_hash)
        rcl.pop2_and_cons()
        rcl.push(foo_hash)
        rcl.push(foo_hash)
        rcl.pop2_and_cons()
        rcl.pop2_and_cons()
        # rcl = ((foo . foo) . (foo . foo))
        # find ALL minimal paths to `foo`
        self.assertEqual(
            rcl.find_paths(foo_hash, serialized_length=20),
            set([bytes([8]), bytes([10]), bytes([12]), bytes([14])]),
        )
