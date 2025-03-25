from typing import Dict, Iterator, List, Optional, Tuple

from .CLVMObject import CLVMStorage
from .tree_path import TreePath, TOP, are_paths_in_order, relative_pointer

from .casts import limbs_for_int
from .object_cache import ObjectCache, treehash, serialized_length
from .serialize import atom_to_byte_iterator, BACK_REFERENCE, CONS_BOX_MARKER


def all_nodes(obj: CLVMStorage) -> Iterator[Tuple[CLVMStorage, TreePath]]:
    to_yield: List[Tuple[CLVMStorage, TreePath]] = [(obj, TOP)]
    while to_yield:
        obj, path = to_yield.pop()
        yield obj, path
        if obj.pair is not None:
            to_yield.append((obj.pair[1], path.right()))
            to_yield.append((obj.pair[0], path.left()))


def sexp_to_byte_iterator_with_backrefs(obj: CLVMStorage) -> Iterator[bytes]:
    thc = ObjectCache(treehash)
    slc = ObjectCache(serialized_length)

    paths_for_hash: Dict[bytes, List[TreePath]] = {}

    for node, path in all_nodes(obj):
        node_tree_hash = thc.get(node)
        paths_for_hash.setdefault(node_tree_hash, []).append(path)

    # in `read_op_stack`:
    #  "P" = "push"
    #  "C" = "pop two objects, create and push a new cons with them"

    read_op_stack = ["P"]

    write_stack: List[Tuple[CLVMStorage, TreePath]] = [(obj, TOP)]

    while write_stack:
        node_to_write, tree_path = write_stack.pop()
        op = read_op_stack.pop()
        assert op == "P"

        node_serialized_length = slc.get(node_to_write)

        node_tree_hash = thc.get(node_to_write)
        possible_paths = paths_for_hash.get(node_tree_hash, [])
        maybe_path = None
        if len(possible_paths) > 1 and node_serialized_length > 3:
            maybe_path = find_short_path(
                tree_path, possible_paths, node_serialized_length
            )
        if maybe_path is not None:
            yield bytes([BACK_REFERENCE])
            yield from atom_to_byte_iterator(bytes(maybe_path))
        elif node_to_write.pair:
            left, right = node_to_write.pair
            yield bytes([CONS_BOX_MARKER])
            write_stack.append((right, tree_path.right()))
            write_stack.append((left, tree_path.left()))
            read_op_stack.append("C")
            read_op_stack.append("P")
            read_op_stack.append("P")
        else:
            atom = node_to_write.atom
            assert atom is not None
            yield from atom_to_byte_iterator(atom)

        while read_op_stack[-1:] == ["C"]:
            read_op_stack.pop()


def find_short_path(
    tree_path: TreePath,
    possible_paths: List[TreePath],
    node_serialized_length: int,
) -> Optional[TreePath]:
    if possible_paths is None or len(possible_paths) == 1:
        return None
    best_size: int = node_serialized_length
    best_path: Optional[TreePath] = None
    for path in possible_paths:
        if are_paths_in_order(tree_path, path):
            break
        # the paths are in order
        relative_path = relative_pointer(path, tree_path)
        size = limbs_for_int(relative_path) + 1
        if best_size is None or size < best_size:
            best_size = size
            best_path = relative_path
    return best_path
