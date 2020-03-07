from pkg_resources import get_distribution, DistributionNotFound

from .runtime_001 import (  # noqa
    run_program,
    to_sexp_f,
    KEYWORD_TO_ATOM,
    KEYWORD_FROM_ATOM,
)

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
     # package is not installed
     __version__ = "unknown"
