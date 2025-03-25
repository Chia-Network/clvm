import io

from clvm.SExp import SExp
from clvm.tree_path import TOP, are_paths_in_order, relative_pointer
from clvm.ser_br import sexp_to_byte_iterator_with_backrefs
from clvm.serialize import sexp_from_stream


def test_tree_path() -> None:
    def check(path: str, value: int) -> None:
        t = TOP.path(path)
        assert t == value

    check("", 1)

    check("f", 2)
    check("r", 3)

    check("ff", 4)
    check("rf", 5)
    check("fr", 6)
    check("rr", 7)

    check("fff", 8)
    check("rff", 9)
    check("frf", 10)
    check("rrf", 11)
    check("ffr", 12)
    check("rfr", 13)
    check("frr", 14)
    check("rrr", 15)

    check("ffff", 16)
    check("rfff", 17)
    check("frff", 18)
    check("rrff", 19)
    check("ffrf", 20)
    check("rfrf", 21)
    check("frrf", 22)
    check("rrrf", 23)
    check("fffr", 24)
    check("rffr", 25)
    check("frfr", 26)
    check("rrfr", 27)
    check("ffrr", 28)
    check("rfrr", 29)
    check("frrr", 30)
    check("rrrr", 31)


def test_are_paths_in_order() -> None:
    assert are_paths_in_order(2, 3) is True
    assert are_paths_in_order(3, 2) is False
    assert are_paths_in_order(2, 1) is True
    assert are_paths_in_order(1, 2) is False
    assert are_paths_in_order(1, 1) is True


def test_relative_pointer() -> None:
    assert relative_pointer(2, 3) == 2
    assert relative_pointer(2, 5) == 2
    assert relative_pointer(2, 7) == 5
    assert relative_pointer(6, 5) == 6
    assert relative_pointer(6, 7) == 13
    assert relative_pointer(14, 13) == 29


def test_sexp_to_byte_iterator_with_backrefs() -> None:
    # This is a test for the function _sexp_to_byte_iterator_with_backrefs

    def check(s: SExp) -> bytes:
        b = b"".join(sexp_to_byte_iterator_with_backrefs(s))
        f = io.BytesIO(b)
        s1 = sexp_from_stream(f, SExp.to, allow_backrefs=True)
        assert s == s1
        return b

    long_atom = b"long_atom" * 10
    s = SExp.to((long_atom, long_atom))
    check(s)

    s = SExp.to([long_atom, (long_atom, long_atom), (long_atom, long_atom)])
    b = check(s)
    print(b.hex())
