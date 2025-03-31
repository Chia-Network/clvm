import unittest

from clvm.SExp import SExp
from clvm.intern_clvm import InternCLVMObject, InternCLVMStorage


class InternCLVMTest(unittest.TestCase): # Renamed class
    def test_add_atom(self) -> None:
        storage = InternCLVMStorage() # Renamed class
        # Empty atom is pre-added
        self.assertEqual(storage._atoms, [b""])
        self.assertEqual(storage._atom_to_index, {b"": 0})

        # Add a new atom
        idx1 = storage.add_atom(b"atom1")
        self.assertEqual(idx1, 1)
        self.assertEqual(storage._atoms, [b"", b"atom1"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"atom1": 1})

        # Add another new atom
        idx2 = storage.add_atom(b"atom2")
        self.assertEqual(idx2, 2)
        self.assertEqual(storage._atoms, [b"", b"atom1", b"atom2"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"atom1": 1, b"atom2": 2})

        # Add a duplicate atom
        idx3 = storage.add_atom(b"atom1")
        self.assertEqual(idx3, 1)  # Should return the existing index
        self.assertEqual(storage._atoms, [b"", b"atom1", b"atom2"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"atom1": 1, b"atom2": 2})

        # Add the empty atom again
        idx0 = storage.add_atom(b"")
        self.assertEqual(idx0, 0)
        self.assertEqual(storage._atoms, [b"", b"atom1", b"atom2"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"atom1": 1, b"atom2": 2})

    def test_add_pair_by_indices(self) -> None:
        storage = InternCLVMStorage() # Renamed class
        # Add atoms needed for pairs
        idx_a = storage.add_atom(b"a")
        idx_b = storage.add_atom(b"b")
        self.assertEqual(idx_a, 1)
        self.assertEqual(idx_b, 2)

        # Add a new pair (a . b) -> (1 . 2)
        pair_idx1 = storage.add_pair_by_indices(idx_a, idx_b)
        self.assertEqual(pair_idx1, -1)  # First pair gets index -1
        self.assertEqual(storage._pairs, [(1, 2)])
        self.assertEqual(storage._pair_to_index, {(1, 2): -1})

        # Add another new pair (b . a) -> (2 . 1)
        pair_idx2 = storage.add_pair_by_indices(idx_b, idx_a)
        self.assertEqual(pair_idx2, -2)
        self.assertEqual(storage._pairs, [(1, 2), (2, 1)])
        self.assertEqual(storage._pair_to_index, {(1, 2): -1, (2, 1): -2})

        # Add a duplicate pair (a . b) -> (1 . 2)
        pair_idx3 = storage.add_pair_by_indices(idx_a, idx_b)
        self.assertEqual(pair_idx3, -1)  # Should return existing index
        self.assertEqual(storage._pairs, [(1, 2), (2, 1)])
        self.assertEqual(storage._pair_to_index, {(1, 2): -1, (2, 1): -2})

        # Add a nested pair (a . (a . b)) -> (1 . -1)
        pair_idx4 = storage.add_pair_by_indices(idx_a, pair_idx1)
        self.assertEqual(pair_idx4, -3)
        self.assertEqual(storage._pairs, [(1, 2), (2, 1), (1, -1)])
        self.assertEqual(storage._pair_to_index, {(1, 2): -1, (2, 1): -2, (1, -1): -3})

    def test_intern_atom(self) -> None:
        storage = InternCLVMStorage() # Renamed class
        sexp_atom = SExp.to(b"hello")
        root_index = storage.intern(sexp_atom)

        self.assertEqual(root_index, 1)  # 0 is b"", 1 should be b"hello"
        self.assertEqual(storage._atoms, [b"", b"hello"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"hello": 1})
        self.assertEqual(storage._pairs, [])
        self.assertEqual(storage._pair_to_index, {})

    def test_intern_simple_pair(self) -> None:
        storage = InternCLVMStorage() # Renamed class
        sexp_pair = SExp.to((b"left", b"right"))
        root_index = storage.intern(sexp_pair)

        # Expected state:
        # Atoms: 0: b"", 1: b"left", 2: b"right"
        # Pairs: -1: (1, 2)
        self.assertEqual(root_index, -1)
        self.assertEqual(storage._atoms, [b"", b"left", b"right"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"left": 1, b"right": 2})
        self.assertEqual(storage._pairs, [(1, 2)])
        self.assertEqual(storage._pair_to_index, {(1, 2): -1})

    def test_intern_nested_pair(self) -> None:
        storage = InternCLVMStorage() # Renamed class
        # (b"a" . (b"b" . b"c"))
        sexp_nested = SExp.to(("a", ("b", "c")))
        root_index = storage.intern(sexp_nested)

        # Expected state:
        # Atoms: 0: b"", 1: b"a", 2: b"b", 3: b"c"
        # Pairs: -1: (2, 3)  => (b"b" . b"c")
        #        -2: (1, -1) => (b"a" . -1)
        self.assertEqual(root_index, -2)
        self.assertEqual(storage._atoms, [b"", b"a", b"b", b"c"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"a": 1, b"b": 2, b"c": 3})
        self.assertEqual(storage._pairs, [(2, 3), (1, -1)])
        self.assertEqual(storage._pair_to_index, {(2, 3): -1, (1, -1): -2})

    def test_intern_interning(self) -> None: # Renamed test
        storage = InternCLVMStorage() # Renamed class
        # Create a structure with repeated elements: (A . (B . (A . C)))
        # A = b"apple", B = b"banana", C = b"cherry"
        sexp_tree = SExp.to(("apple", ("banana", ("apple", "cherry"))))
        root_index = storage.intern(sexp_tree)

        # Expected state:
        # Atoms: 0: b"", 1: b"apple", 2: b"banana", 3: b"cherry"
        # Pairs: -1: (1, 3) => (A . C)
        #        -2: (2, -1) => (B . (A . C))
        #        -3: (1, -2) => (A . (B . (A . C)))
        self.assertEqual(root_index, -3)
        self.assertEqual(storage._atoms, [b"", b"apple", b"banana", b"cherry"])
        self.assertEqual(
            storage._atom_to_index,
            {b"": 0, b"apple": 1, b"banana": 2, b"cherry": 3},
        )
        # Check that atom "apple" (index 1) was only stored once
        self.assertEqual(len(storage._atoms), 4)

        self.assertEqual(storage._pairs, [(1, 3), (2, -1), (1, -2)])
        self.assertEqual(storage._pair_to_index, {(1, 3): -1, (2, -1): -2, (1, -2): -3})
        # Check that the pair (A . C) (index -1) was only stored once
        self.assertEqual(len(storage._pairs), 3)

    def test_intern_shared_subtree(self) -> None:
        storage = InternCLVMStorage() # Renamed class
        # Create a structure with a shared subtree: ((A . B) . (A . B))
        shared_pair = SExp.to(("a", "b"))
        sexp_tree = SExp.to((shared_pair, shared_pair))

        root_index = storage.intern(sexp_tree)

        # Expected state:
        # Atoms: 0: b"", 1: b"a", 2: b"b"
        # Pairs: -1: (1, 2) => (A . B)
        #        -2: (-1, -1) => ((A . B) . (A . B))
        self.assertEqual(root_index, -2)
        self.assertEqual(storage._atoms, [b"", b"a", b"b"])
        self.assertEqual(storage._atom_to_index, {b"": 0, b"a": 1, b"b": 2})
        self.assertEqual(len(storage._atoms), 3)

        self.assertEqual(storage._pairs, [(1, 2), (-1, -1)])
        self.assertEqual(storage._pair_to_index, {(1, 2): -1, (-1, -1): -2})
        # Check that the pair (A . B) (index -1) was only stored once (interned)
        self.assertEqual(len(storage._pairs), 2)

    def test_intern_object_atom(self) -> None: # Renamed test
        storage = InternCLVMStorage() # Renamed class
        atom_idx = storage.add_atom(b"test")
        intern_obj = InternCLVMObject(storage, atom_idx) # Renamed class & var

        self.assertEqual(intern_obj.atom, b"test")
        self.assertIsNone(intern_obj.pair)

    def test_intern_object_pair(self) -> None: # Renamed test
        storage = InternCLVMStorage() # Renamed class
        idx_a = storage.add_atom(b"a")
        idx_b = storage.add_atom(b"b")
        pair_idx = storage.add_pair_by_indices(idx_a, idx_b)
        intern_obj = InternCLVMObject(storage, pair_idx) # Renamed class & var

        self.assertIsNone(intern_obj.atom)
        pair = intern_obj.pair
        self.assertIsNotNone(pair)
        assert pair is not None  # for type checking

        left, right = pair
        self.assertIsInstance(left, InternCLVMObject) # Renamed class
        self.assertIsInstance(right, InternCLVMObject) # Renamed class
        self.assertEqual(left.atom, b"a")
        self.assertIsNone(left.pair)
        self.assertEqual(right.atom, b"b")
        self.assertIsNone(right.pair)

    def test_intern_object_reconstruction(self) -> None: # Renamed test
        storage = InternCLVMStorage() # Renamed class
        # Original SExp: (A . (B . (A . C)))
        sexp_a = SExp.to(b"apple")
        sexp_b = SExp.to(b"banana")
        sexp_c = SExp.to(b"cherry")
        original_sexp = SExp.to((sexp_a, (sexp_b, (sexp_a, sexp_c))))

        # Add to storage
        root_index = storage.intern(original_sexp)

        # Create InternCLVMObject wrapper
        intern_root = InternCLVMObject(storage, root_index) # Renamed class & var

        # Reconstruct SExp from InternCLVMObject
        # SExp.to() should handle any CLVMStorage object
        reconstructed_sexp = SExp.to(intern_root)

        # Verify equality
        self.assertEqual(original_sexp, reconstructed_sexp)
        self.assertEqual(original_sexp.as_python(), reconstructed_sexp.as_python())

        # Manual traversal check
        self.assertIsNone(intern_root.atom)
        pair1 = intern_root.pair
        self.assertIsNotNone(pair1)
        assert pair1 is not None
        left1, right1 = pair1
        self.assertEqual(left1.atom, b"apple")  # A
        self.assertIsNone(left1.pair)

        self.assertIsNone(right1.atom)  # (B . (A . C))
        pair2 = right1.pair
        self.assertIsNotNone(pair2)
        assert pair2 is not None
        left2, right2 = pair2
        self.assertEqual(left2.atom, b"banana")  # B
        self.assertIsNone(left2.pair)

        self.assertIsNone(right2.atom)  # (A . C)
        pair3 = right2.pair
        self.assertIsNotNone(pair3)
        assert pair3 is not None
        left3, right3 = pair3
        self.assertEqual(left3.atom, b"apple")  # A
        self.assertIsNone(left3.pair)
        self.assertEqual(right3.atom, b"cherry")  # C
        self.assertIsNone(right3.pair)

    def test_intern_object_reconstruction_shared(self) -> None: # Renamed test
        storage = InternCLVMStorage() # Renamed class
        # Original SExp: ((A . B) . (A . B))
        sexp_a = SExp.to(b"a")
        sexp_b = SExp.to(b"b")
        shared_pair_sexp = SExp.to((sexp_a, sexp_b))
        original_sexp = SExp.to((shared_pair_sexp, shared_pair_sexp))

        # Add to storage
        root_index = storage.intern(original_sexp)
        self.assertEqual(len(storage._pairs), 2)  # Ensure pair was interned

        # Create InternCLVMObject wrapper
        intern_root = InternCLVMObject(storage, root_index) # Renamed class & var

        # Reconstruct SExp from InternCLVMObject
        reconstructed_sexp = SExp.to(intern_root)

        # Verify equality
        self.assertEqual(original_sexp, reconstructed_sexp)
        self.assertEqual(original_sexp.as_python(), reconstructed_sexp.as_python())

        # Manual traversal check
        self.assertIsNone(intern_root.atom)
        pair1 = intern_root.pair
        self.assertIsNotNone(pair1)
        assert pair1 is not None
        left1, right1 = pair1  # Both should be (A . B)

        self.assertIsNone(left1.atom)
        pair_l = left1.pair
        self.assertIsNotNone(pair_l)
        assert pair_l is not None
        self.assertEqual(pair_l[0].atom, b"a")
        self.assertEqual(pair_l[1].atom, b"b")

        self.assertIsNone(right1.atom)
        pair_r = right1.pair
        self.assertIsNotNone(pair_r)
        assert pair_r is not None
        self.assertEqual(pair_r[0].atom, b"a")
        self.assertEqual(pair_r[1].atom, b"b")

        # Check that the underlying InternCLVMObject instances for the shared part might be different
        # (as they are created on demand), but represent the same structure.
        # We don't strictly need them to be the same instance, just equal.
        # Compare using SExp.to() which implements structural equality.
        self.assertEqual(SExp.to(left1), SExp.to(right1))
