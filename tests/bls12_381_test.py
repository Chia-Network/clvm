import unittest

from chia_rs import G1Element, PrivateKey

bls12_381_generator = G1Element.generator()


class BLS12_381_Test(unittest.TestCase):
    def test_stream(self) -> None:
        for _ in range(1, 64):
            p = PrivateKey.from_bytes(_.to_bytes(32, "big")).get_g1()
            blob = bytes(p)
            p1 = G1Element.from_bytes(blob)
            self.assertEqual(len(blob), 48)
            self.assertEqual(p, p1)
