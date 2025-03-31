from typing import Dict, List, Optional, Tuple

from .CLVMObject import CLVMStorage


class DedupCLVMStorage:
    """
    A negative index means it's a pair.
    """

    def __init__(self) -> None:
        self._atoms: List[bytes] = [b""]
        self._pairs: List[Tuple[int, int]] = []
        self._atom_to_index: Dict[bytes, int] = {}
        self._pair_to_index: Dict[Tuple[int, int], int] = {}

    def add_atom(self, atom: bytes) -> int:
        if atom in self._atoms:
            return self._atoms.index(atom)
        self._atoms.append(atom)
        return len(self._atoms) - 1

    def add_pair_by_indices(self, left: int, right: int) -> int:
        pair = (left, right)
        if pair in self._pair_to_index:
            return self._pair_to_index[pair]
        self._pairs.append(pair)
        negative_index = -len(self._pairs)
        return negative_index

    def add_clvm(self, obj: CLVMStorage) -> int:
        added_stack: List[int] = []
        to_add: List[CLVMStorage] = [obj]
        operator_stack: List[str] = ["Z"]  # "Z" = "canonicalize", "J" = "join"
        while operator_stack:
            op = operator_stack.pop()
            if op == "Z":
                o = to_add.pop()
                if o.pair is None:
                    assert o.atom is not None
                    added_stack.append(self.add_atom(o.atom))
                else:
                    operator_stack.append("Z")
                    operator_stack.append("Z")
                    operator_stack.append("J")
                    to_add.append(o.pair[0])
                    to_add.append(o.pair[1])
            else:  # op == "J"
                right = added_stack.pop()
                left = added_stack.pop()
                added_stack.append(self.add_pair_by_indices(left, right))
        return added_stack[0]


class DedupCLVMObject(CLVMStorage):
    def __init__(self, dedup_storage: DedupCLVMStorage, index: int):
        self._dedup_storage = dedup_storage
        self._index = index
        self.atom = None
        if index >= 0:
            self.atom = dedup_storage._atoms[index]

    @property
    def pair(self) -> Optional[Tuple[CLVMStorage, CLVMStorage]]:
        if self._index < 0:
            left, right = self._dedup_storage._pairs[-self._index - 1]
            return (
                DedupCLVMObject(self._dedup_storage, left),
                DedupCLVMObject(self._dedup_storage, right),
            )

        return None
