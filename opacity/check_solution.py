from .compile import compile_to_sexp
from .reduce import reduce


def build_check_solution_sexp():
    CHECK_SOLUTION_SCRIPT = """
    (reduce (and
        (quote (reduce x0 x1))
        (quasiquote (equal (sha256 (wrap x0)) (unquote x0)))
        )
        x1
    )
    """
    return compile_to_sexp(CHECK_SOLUTION_SCRIPT)


CHECK_SOLUTION_SEXP = build_check_solution_sexp()


def check_solution(script_hash, solution_sexp):
    return reduce(CHECK_SOLUTION_SEXP, [script_hash, solution_sexp])
