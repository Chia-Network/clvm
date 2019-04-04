## LEGACY FILE: DO NOT USE. IT WILL GO AWAY SOON

import importlib

from .core import make_reduce_f
from .core_operators import minimal_ops
from .keywords import KEYWORD_TO_INT


def make_standard_reduce_and_rewrite(rewrite_actions_module=None):
    operator_lookup = minimal_ops(KEYWORD_TO_INT)

    reduce_f = make_reduce_f(operator_lookup, KEYWORD_TO_INT)

    if rewrite_actions_module:
        mod = importlib.import_module(rewrite_actions_module)
        rewrite_f = mod.make_rewrite_f(KEYWORD_TO_INT, reduce_f)
        d = {}
        for keyword, op_f in mod.DOMAIN_OPERATORS:
            d[KEYWORD_TO_INT[keyword]] = op_f
        operator_lookup.update(d)
    return reduce_f, rewrite_f


STANDARD_REDUCE_F, STANDARD_REWRITE_F = make_standard_reduce_and_rewrite("opacity.standard_rewrite")


def default_reduce_f(self, form, env):
    new_form = STANDARD_REWRITE_F(STANDARD_REWRITE_F, form)
    return STANDARD_REDUCE_F(STANDARD_REDUCE_F, new_form, env)


def reduce(form, env):
    return default_reduce_f(default_reduce_f, form, env)
