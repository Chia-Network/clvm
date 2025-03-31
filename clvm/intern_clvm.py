"""
This module provides classes for representing CLVM objects in an interned
manner. It aims to reduce memory usage by storing each unique atom and pair
only once.

`InternCLVMStorage` manages the storage of unique atoms and pairs, assigning
indices to them. Positive indices represent atoms, and negative indices
represent pairs.

`InternCLVMObject` provides a `CLVMStorage`-compatible interface to access
the interned objects stored within an `InternCLVMStorage` instance.
"""

from typing import Dict, List, Optional, Tuple

from .CLVMObject import CLVMStorage


class InternCLVMStorage:
    """
    Manages the storage of unique atoms and pairs for interning.

    Atoms are stored in a list (`_atoms`), and their indices are positive integers
    starting from 0. The empty byte string `b""` is implicitly at index 0.
    Pairs are stored in a list (`_pairs`) as tuples of indices (left, right).
    Their indices are negative integers starting from -1.

    Dictionaries (`_atom_to_index`, `_pair_to_index`) map the actual atoms/pair
    indices back to their storage index for quick lookups and interning.
    """

    def __init__(self) -> None:
        """Initializes the storage with the empty atom at index 0."""
        self._atoms: List[bytes] = [b""]
        self._pairs: List[Tuple[int, int]] = []
        # Map atom bytes to their positive index in _atoms
        self._atom_to_index: Dict[bytes, int] = {b"": 0}
        # Map (left_idx, right_idx) tuples to their negative index (-1-based)
        self._pair_to_index: Dict[Tuple[int, int], int] = {}

    def add_atom(self, atom: bytes) -> int:
        """
        Adds an atom to the storage if it's not already present (part of interning).

        Args:
            atom: The byte string atom to add.

        Returns:
            The positive integer index of the atom in the storage.
        """
        if atom in self._atom_to_index:
            return self._atom_to_index[atom]
        index = len(self._atoms)
        self._atoms.append(atom)
        self._atom_to_index[atom] = index
        return index

    def add_pair_by_indices(self, left: int, right: int) -> int:
        """
        Adds a pair represented by the indices of its left and right children
        if it's not already present (part of interning).

        Args:
            left: The index (positive for atom, negative for pair) of the left child.
            right: The index (positive for atom, negative for pair) of the right child.

        Returns:
            The negative integer index representing the pair in the storage.
            The index is calculated as `-len(_pairs)` after adding, effectively
            starting from -1 for the first pair added.
        """
        pair_indices = (left, right)
        if pair_indices in self._pair_to_index:
            return self._pair_to_index[pair_indices]
        self._pairs.append(pair_indices)
        # Negative indices represent pairs. The first pair added gets index -1.
        negative_index = -len(self._pairs)
        self._pair_to_index[pair_indices] = negative_index
        return negative_index

    def intern(self, obj: CLVMStorage) -> int:
        """
        Recursively interns a CLVM object (and its children) into the storage,
        returning its unique index.

        Interning ensures that each unique atom and pair structure is stored only once.

        This uses a non-recursive approach with stacks to traverse the CLVM object tree.
        Since the CLVM object structure can be deeply nested, a recursive approach
        could lead to a stack overflow. This iterative approach avoids that.

        `to_process` holds the CLVM objects yet to be processed.
        `operator_stack` controls the processing logic:
            - "I" (Intern): Process the next object from `to_process`. If it's an
              atom, add it using `add_atom` and push its index to `result_stack`.
              If it's a pair, push its children to `to_process` and schedule them
              for interning ("I") followed by joining ("J").
            - "J" (Join): Pop the indices of the right and left children from
              `result_stack`, create a pair using `add_pair_by_indices`, and push
              the resulting pair index back onto `result_stack`.
        `result_stack` stores the indices (positive for atoms, negative for pairs)
        of the processed nodes.

        Args:
            obj: The CLVMStorage object to intern.

        Returns:
            The root index (positive for atom, negative for pair) of the interned
            object within the storage.
        """
        result_stack: List[int] = []  # Stores indices of processed nodes
        to_process: List[CLVMStorage] = [obj]  # CLVM objects to process
        operator_stack: List[str] = ["I"]  # Operations: "I" = intern, "J" = join
        while operator_stack:
            op = operator_stack.pop()
            if op == "I":
                o = to_process.pop()
                if o.pair is None:
                    # It's an atom
                    assert o.atom is not None
                    atom_index = self.add_atom(o.atom)
                    result_stack.append(atom_index)
                else:
                    # It's a pair. Schedule children processing and then joining.
                    # Order matters: process right, then left, then join.
                    operator_stack.append("J")  # Join the results later
                    operator_stack.append("I")  # Process right child
                    operator_stack.append("I")  # Process left child
                    to_process.append(o.pair[1])  # Right child
                    to_process.append(o.pair[0])  # Left child
            else:  # op == "J"
                # Join the last two processed indices (right then left)
                right_index = result_stack.pop()
                left_index = result_stack.pop()
                pair_index = self.add_pair_by_indices(left_index, right_index)
                result_stack.append(pair_index)

        # The final index on the stack is the root index of the added object
        assert len(result_stack) == 1
        return result_stack[0]

    def __str__(self) -> str:
        """Returns a string representation of the storage for debugging."""
        return f"InternCLVMStorage(atom_count={len(self._atoms)}, pair_count={len(self._pairs)})"

    def __repr__(self) -> str:
        """Returns a string representation of the storage for debugging."""
        return str(self)


class InternCLVMObject(CLVMStorage):
    """
    A CLVMStorage-compatible wrapper around an object within InternCLVMStorage.

    This class allows accessing an interned CLVM object structure using the
    standard `atom` and `pair` properties, reconstructing pairs on demand based
    on the stored indices.
    """

    def __init__(self, intern_storage: InternCLVMStorage, index: int):
        """
        Initializes the wrapper object.

        Args:
            intern_storage: The underlying storage containing the interned data.
            index: The index (positive for atom, negative for pair) of the object
                   within the `intern_storage`.
        """
        self._intern_storage = intern_storage
        self._index = index
        self.atom: Optional[bytes] = None
        # If the index is non-negative, it represents an atom.
        if index >= 0:
            self.atom = intern_storage._atoms[index]
        # The `pair` property handles negative indices dynamically.

    @property
    def pair(self) -> Optional[Tuple[CLVMStorage, CLVMStorage]]:
        """
        Provides the pair tuple if this object represents a pair.

        If the internal index is negative, it looks up the corresponding pair
        indices in the `InternCLVMStorage` and returns a tuple of new
        `InternCLVMObject` instances representing the children.

        Returns:
            A tuple (left_child, right_child) if this object is a pair,
            otherwise None.
        """
        if self._index < 0:
            # Negative index means it's a pair. Convert back to list index.
            pair_list_index = -self._index - 1
            left_idx, right_idx = self._intern_storage._pairs[pair_list_index]
            # Recursively create InternCLVMObject wrappers for the children
            left_child = InternCLVMObject(self._intern_storage, left_idx)
            right_child = InternCLVMObject(self._intern_storage, right_idx)
            return (left_child, right_child)

        # Positive index means it's an atom, so no pair.
        return None

    def __str__(self) -> str:
        """Returns a string representation of the object for debugging."""
        if self.atom is not None:
            # Use SExp.to for a standard CLVM representation
            return repr(SExp.to(self))
        # For pairs, rely on SExp representation as well to handle nesting
        return repr(SExp.to(self))

    def __repr__(self) -> str:
        """Returns a string representation of the object for debugging."""
        # Use SExp for a consistent and readable representation
        return repr(SExp.to(self))


def intern_clvm(obj: CLVMStorage) -> InternCLVMObject:
    """
    Interns the given CLVM object and returns an `InternCLVMObject` wrapper.

    Args:
        obj: The CLVM object to intern.

    Returns:
        An `InternCLVMObject` instance representing the interned object.
    """
    intern_storage = InternCLVMStorage()
    root_index = intern_storage.intern(obj)
    return InternCLVMObject(intern_storage, root_index)

# Need to import SExp late to avoid circular dependency
from .SExp import SExp # noqa E402
