from . import core_operators

from .ReduceError import ReduceError
from .SExp import SExp

CORE_KEYWORDS = ". quote reduce cons first rest type var env_raw is_null get_raw raise equal".split()

CORE_KEYWORDS = (
    ". choose1 aggsig point_add assert_output pubkey_for_exp and type equal "
    "sha256 reduce + * - / wrap unwrap list quote quasiquote unquote get env "
    "case is_atom list1 "
    "cons first rest list type is_null var apply eval "
    "macro_expand reduce_var reduce_bytes reduce_list if not bool or map "
    "get_raw env_raw has_unquote get_default "
    "first_true raise reduce_raw rewrite rewrite_op concat ").split()


KEYWORD_FROM_INT = CORE_KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}


def make_reduce_f(operator_lookup, keyword_to_int):

    keyword_from_int = {v: k for k, v in keyword_to_int.items()}

    QUOTE_KEYWORD = keyword_to_int["quote"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]
    ENV_RAW_KEYWORD = keyword_to_int["env_raw"]

    def reduce_core(reduce_f, form, env):
        if not form.is_list():
            raise ReduceError("%s is not a list" % form)

        if len(form) == 0:
            raise ReduceError("reduce_list cannot handle empty list")

        first_item = form[0]

        if not first_item.is_bytes():
            raise ReduceError("non-byte atom %s in first element of list" % first_item)

        f_index = first_item.as_int()

        # special form QUOTE

        if f_index == QUOTE_KEYWORD:
            if len(form) != 2:
                raise ReduceError("quote requires exactly 1 parameter, got %d" % (len(form) - 1))
            return form[1]

        # TODO: rewrite with cons, rest, etc.
        args = SExp([reduce_f(reduce_f, _, env) for _ in form[1:]])

        # keyword REDUCE

        if f_index == REDUCE_KEYWORD:
            if len(args) != 2:
                raise ReduceError("reduce_list requires 2 parameters, got %d" % len(args))
            return reduce_f(reduce_f, args[0], args[1])

        # keyword ENV_RAW

        if f_index == ENV_RAW_KEYWORD:
            if len(form) != 1:
                raise ReduceError("env_raw requires no parameters, got %d" % (len(form) - 1))
            return env

        # special form APPLY

        f = operator_lookup.get(f_index)
        if f:
            return f(args)

        msg = "unknown function index %d" % f_index
        if f_index in keyword_from_int:
            msg += ' for keyword "%s"' % keyword_from_int[f_index]
        raise ReduceError(msg)

    return reduce_core


OPERATOR_LOOKUP = {KEYWORD_TO_INT[op]: getattr(
    core_operators, "op_%s" % op, None) for op in KEYWORD_TO_INT.keys()}
do_reduce_f = make_reduce_f(OPERATOR_LOOKUP, KEYWORD_TO_INT)
do_reduce_f.operator_lookup = OPERATOR_LOOKUP
