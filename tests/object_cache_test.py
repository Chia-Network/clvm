import unittest

from clvm.object_cache import ObjectCache, treehash, serialized_length

from clvm_tools.binutils import assemble


class ObjectCacheTest(unittest.TestCase):
    def check(self, obj_text: str, expected_hash: str, expected_length: int) -> None:
        obj = assemble(obj_text)
        th = ObjectCache(treehash)
        self.assertEqual(th.get(obj).hex(), expected_hash)
        sl = ObjectCache(serialized_length)
        self.assertEqual(sl.get(obj), expected_length)

    def test_various(self) -> None:
        self.check(
            "0x00",
            "47dc540c94ceb704a23875c11273e16bb0b8a87aed84de911f2133568115f254",
            1,
        )

        self.check(
            "0", "4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a", 1
        )

        self.check(
            "foo", "0080b50a51ecd0ccfaaa4d49dba866fe58724f18445d30202bafb03e21eef6cb", 4
        )

        self.check(
            "(foo . bar)",
            "c518e45ae6a7b4146017b7a1d81639051b132f1f5572ce3088a3898a9ed1280b",
            9,
        )

        self.check(
            "(this is a longer test of a deeper tree)",
            "0a072d7d860d77d8e290ced0fdb29a271198ca3db54d701c45d831e3aae6422c",
            47,
        )
