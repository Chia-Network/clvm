from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clvm.SExp import SExp


class EvalError(Exception):
    def __init__(self, message: str, sexp: SExp) -> None:
        super().__init__(message)
        self._sexp = sexp
