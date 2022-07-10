from clvm.SExp import SExp


class EvalError(Exception):
    def __init__(self, message: str, sexp: SExp) -> None:
        super().__init__(message)
        self._sexp = sexp
