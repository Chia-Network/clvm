import unittest

from clvm.ecdsa.bls12_381 import bls12_381_generator
from clvm.casts import bls12_381_from_bytes, bls12_381_to_bytes


class BLS12_381_Test(unittest.TestCase):

    def test_stream(self):
        for _ in range(1, 64):
            p = bls12_381_generator * _
            blob = bls12_381_to_bytes(p)
            p1 = bls12_381_from_bytes(blob)
            self.assertEqual(len(blob), 48)
            self.assertEqual(p, p1)
