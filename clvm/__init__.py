from pkg_resources import get_distribution, DistributionNotFound

from .SExp import SExp
from .operators import (  # noqa
    KEYWORD_TO_ATOM,
    KEYWORD_FROM_ATOM,
)
from .runtime_001 import run_program  # noqa

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

to_sexp_f = SExp.to  # noqa
