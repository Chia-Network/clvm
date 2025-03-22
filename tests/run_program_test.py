import unittest

from clvm.run_program import msb_mask


class BitTest(unittest.TestCase):
    def test_msb_mask(self) -> None:
        self.assertEqual(msb_mask(0x0), 0x0)
        self.assertEqual(msb_mask(0x01), 0x01)
        self.assertEqual(msb_mask(0x02), 0x02)
        self.assertEqual(msb_mask(0x04), 0x04)
        self.assertEqual(msb_mask(0x08), 0x08)
        self.assertEqual(msb_mask(0x10), 0x10)
        self.assertEqual(msb_mask(0x20), 0x20)
        self.assertEqual(msb_mask(0x40), 0x40)
        self.assertEqual(msb_mask(0x80), 0x80)

        self.assertEqual(msb_mask(0x44), 0x40)
        self.assertEqual(msb_mask(0x2A), 0x20)
        self.assertEqual(msb_mask(0xFF), 0x80)
        self.assertEqual(msb_mask(0x0F), 0x08)
