import os

from .intstream import from_bytes

from .Curve import Curve
from .Point import Point


class Generator(Curve, Point):
    def __new__(self, p, a, b, basis, order):
        # since Generator extends tuple (via Point), we need to override __new__
        return tuple.__new__(self, basis)

    def __init__(self, p, a, b, basis, order, entropy_f=os.urandom):
        """
        Set up a group with generator basis for the curve y^2 = x^3 + x*a + b (mod p).
        The order is the order of the group (it's generally predetermined for a given curve;
        how it's calculated is complicated).
        The entropy function creates a blinding factor, to mitigate side channel attacks.
        """
        Curve.__init__(self, p, a, b, order)
        Point.__init__(self, basis[0], basis[1], self)
        self._powers = []
        Gp = self
        for _ in range(256):
            self._powers.append(Gp)
            Gp += Gp
        assert p % 4 == 3, "p % 4 must be 3 due to modular_sqrt optimization"
        self._mod_sqrt_power = (p + 1) // 4
        self._blinding_factor = from_bytes(entropy_f(32)) % self._order
        self._minus_blinding_factor_g = self.raw_mul(-self._blinding_factor)

    def modular_sqrt(self, a):
        "Return n where n * n == a (mod p). If no such n exists, an arbitrary value will be returned."
        return pow(a, self._mod_sqrt_power, self._p)

    def inverse(self, a):
        "Return n such that a * n == 1 (mod p)."
        return self.inverse_mod(a, self._order)

    def points_for_x(self, x):
        """
        Return (p0, p1) where for each p is a point with given x coordinate
        and p0's y value is even

        To get a point with particular parity, use something like
        ```points_for_x(x)[1 if is_y_supposed_to_be_odd else 0]```
        """
        p = self._p
        alpha = (pow(x, 3, p) + self._a * x + self._b) % p
        y0 = self.modular_sqrt(alpha)
        if y0 == 0:
            raise ValueError("no y value for %d" % x)
        p0, p1 = [self.Point(x, _) for _ in (y0, p - y0)]
        if y0 & 1 == 0:
            return (p0, p1)
        return (p1, p0)

    def possible_public_pairs_for_signature(self, value, signature, y_parity=None):
        """
        yield a list of possible points (public keys) that generated the signature for the given
        value. If y_parity is not None, only one value will be returned; otherwise two values.
        """
        r, s = signature

        try:
            points = self.points_for_x(r)
        except ValueError:
            return []

        if y_parity is not None:
            if y_parity & 1:
                points = points[1:]
            else:
                points = points[:1]

        inv_r = self.inverse(r)
        s_over_r = s * inv_r
        minus_E_over_r = -(inv_r * value) * self
        try:
            return [s_over_r * p + minus_E_over_r for p in points]
        except ValueError:
            return []

    def raw_mul(self, e):
        """Multiply the generator by an integer."""
        e %= self._order
        P = self._infinity
        for bit in range(256):
            # add the power of the generator every time to make it more time-deterministic
            a = [P, P + self._powers[bit]]
            # choose the correct result
            P = a[e & 1]
            e >>= 1
        return P

    def __mul__(self, e):
        """Multiply the generator by an integer. Uses the blinding factor."""
        return self.raw_mul(e + self._blinding_factor) + self._minus_blinding_factor_g

    def __rmul__(self, e):
        """Multiply the generator by an integer."""
        return self.__mul__(e)
