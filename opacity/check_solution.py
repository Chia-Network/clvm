import binascii

from .compile import compile_to_sexp
from .reduce import reduce



def build_check_solution_sexp():
    CHECK_SOLUTION_SCRIPT = """
    (
        (quote (reduce (unwrap x0) (unwrap x1)))
        (quote ((equal (sha256 x0) (unquote x0))))
    )
    """
    return compile_to_sexp(CHECK_SOLUTION_SCRIPT)


CHECK_SOLUTION_SEXP = build_check_solution_sexp()


def check_solution(script_hash, solution_sexp):
    script_sexp = reduce(CHECK_SOLUTION_SEXP, [script_hash])
    reductions = reduce(script_sexp, solution_sexp)
    return reductions
