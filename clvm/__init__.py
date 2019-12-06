from setuptools_scm import get_version

from .runtime_001 import eval_f, to_sexp_f, KEYWORD_TO_ATOM, KEYWORD_FROM_ATOM  # noqa

__version__ = version = get_version()
