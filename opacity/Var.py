from dataclasses import dataclass


@dataclass
class Var:
    index: int

    def __repr__(self):
        return "x%d" % self.index
