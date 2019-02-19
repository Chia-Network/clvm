import binascii
import hashlib
import unittest

from opacity.casts import bls12_381_to_bytes
from opacity.compile import parse_macros, compile_to_sexp, disassemble, disassemble_sexp
from opacity.ecdsa.bls12_381 import bls12_381_generator
from opacity.reduce import reduce
from opacity.SExp import SExp

# taproot with a locktime


MACRO_TEXT = """
(
  (macro (pay_to_taproot P x0 x1 x2 x3 x4)
    (and (choose1 x0
       (aggsig x1 (wrap x2)) ; standard branch
       (equal x1 (point_add (pubkey_for_exp (sha256 x4 (wrap x2))) x4)) ; taproot branch
     )
     (reduce x2 x3)
     (equal x1 P) ; x1 = P1 = P + hash(P||S)
    )
  )
  (macro (timelock x0 x1 x2 x3)
    (choose1
      x0  ; 1 for timelock condition (x2), 0 for non-timelock (x1)
      x1  ; non-timelock condition
      (and
        x2  ; timelock condition
        (assert_confirm_timestamp_exceeds x3)
      )
    )
  )
)
"""


MACROS = parse_macros(MACRO_TEXT)


class TaprootTest(unittest.TestCase):
    def test_taproot_simple(self):
        # in this case, P = bls12_381_generator * 1
        # magic underlying script S = "(assert_output 500)"
        P1 = bls12_381_generator * 1
        P1_bin = bls12_381_to_bytes(P1)
        S_text = "(assert_output 500)"
        S_bin = compile_to_sexp(S_text)
        taproot_hash = hashlib.sha256(P1_bin + S_bin.as_bin()).digest()
        taproot_hash_as_exp = int.from_bytes(taproot_hash, byteorder="big")
        P = P1 + (bls12_381_generator * taproot_hash_as_exp)
        P_bin = bls12_381_to_bytes(P)
        P_hex = binascii.hexlify(P_bin).decode("utf8")

        taproot_script_text = "(pay_to_taproot 0x%s x0 x1 x2 x3 x4)" % P_hex
        main_script = compile_to_sexp(taproot_script_text, macros=MACROS)

        # solve using taproot
        solution = [1, P_bin, S_bin, SExp(0), P1_bin]
        reductions = reduce(main_script, SExp(solution))
        d = disassemble_sexp(reductions)
        self.assertEqual(d, "(and 1 %s 1)" % S_text)

        # solve signature, no taproot
        x2 = compile_to_sexp("(assert_output 600)")
        solution = [0, P_bin, x2, SExp(0)]
        reductions = reduce(main_script, SExp(solution))
        d = disassemble_sexp(reductions)
        d1 = "(and (aggsig 0x%s 0x%s) %s 1)" % (
            P_hex, binascii.hexlify(x2.as_bin()).decode("utf8"), disassemble(x2))
        self.assertEqual(d, d1)
