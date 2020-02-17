from setuptools_scm import get_version

from .runtime_001 import (  # noqa
    run_program,
    to_sexp_f,
    KEYWORD_TO_ATOM,
    KEYWORD_FROM_ATOM,
)

try:
    __version__ = get_version()
except LookupError:
    __version__ = "unknown"
