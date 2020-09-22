import unittest

from blspy import G1Element


bls12_381_generator = G1Element.generator()


class BLS12_381_Test(unittest.TestCase):

    def test_stream(self):
        for _ in range(1, 64):
            p = bls12_381_generator * _
            blob = bytes(p)
            p1 = G1Element.from_bytes(blob)
            self.assertEqual(len(blob), 48)
            self.assertEqual(p, p1)
