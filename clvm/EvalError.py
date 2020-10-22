class EvalError(Exception):
    def __init__(self, message, sexp):
        super().__init__(message)
        self._sexp = sexp
