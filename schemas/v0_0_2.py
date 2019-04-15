from opacity.SExp import SExp

from opacity.compile import compile_to_sexp
from opacity.core import do_reduce_f as core_reduce_f

from .more_operators import (
    op_add, op_multiply, op_unwrap, op_wrap, op_sha256, op_subtract
)


KEYWORDS = (
    ". choose1 aggsig point_add assert_output pubkey_for_exp and type equal "
    "sha256 reduce + * - / wrap unwrap list quote quasiquote unquote get env "
    "case is_atom list1 "
    "cons first rest list type is_null var apply eval "
    "macro_expand reduce_var reduce_bytes reduce_list if not bool or map "
    "get_raw env_raw has_unquote get_default "
    "first_true raise reduce_raw rewrite rewrite_op concat ").split()


KEYWORD_FROM_INT = KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}


DERIVED_OPERATORS = [
    ("if",
        "(cons (quote #reduce) (cons (cons (quote #get_raw) (cons (cons (quote #quote) "
        "(cons (rest (env_raw)) (quote ()))) (cons (cons (quote #equal) (cons (get_raw "
        "(env_raw) (quote 0)) (quote ((quote 0))))) (quote ())))) (quote ((env_raw)))))"),
    ("list",
        "(if (is_null (env_raw)) "
        "(quote (quote ())) "
        "(cons (quote #cons) (cons (first (env_raw)) "
        "(cons (cons (quote #list) (rest (env_raw))) (quote ())))))"),
    ("bool", "(quasiquote (if (unquote x0) (quote 1) (quote 0)))"),
    ("not", "(quasiquote (if (unquote x0) (quote 0) (quote 1)))"),
    ("choose1",
        "(list #reduce (list #get_raw (cons #quote (list (rest (env_raw)))) x0) (quote (env_raw)))"),
    ("env",
        "(cons #get (cons (cons #env_raw (quote ())) (env_raw)))"),
    ("get",
        "(reduce (get_raw "
        "(quote ((cons (quote #get) "
        "(cons (cons (quote #get_raw) (cons (get_raw (env_raw) (quote 0)) "
        "(cons (get_raw (env_raw) (quote 1)) (quote ())))) "
        "(rest (rest (env_raw))))) (get_raw (env_raw) (quote 0)))) "
        "(is_null (rest (env_raw)))) (env_raw))"),
    ("map",
        "(quasiquote (reduce (quote (if (is_null x1) (quote ())"
        " (cons (reduce x0 (list (first x1))) (map x0 (rest x1))))) (list (unquote x0) (unquote x1))))"),
    ("assert_output", "(quasiquote (quote (unquote (cons #assert_output (env_raw)))))"),
    ("rewrite", "(quasiquote (rewrite_op (quote (unquote x0))))"),
]


def make_rewrite_f(keyword_to_int, reduce_f, reduce_constants=True):

    ENV_RAW_KEYWORD = keyword_to_int["env_raw"]
    GET_RAW_KEYWORD = keyword_to_int["get_raw"]
    LIST_KEYWORD = keyword_to_int["list"]
    QUASIQUOTE_KEYWORD = keyword_to_int["quasiquote"]
    QUOTE_KEYWORD = keyword_to_int["quote"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]
    UNQUOTE_KEYWORD = keyword_to_int["unquote"]

    optimize_form = make_optimize_form_f(keyword_to_int, reduce_f)

    derived_operators = {}
    for kw, program in DERIVED_OPERATORS:
        derived_operators[keyword_to_int[kw]] = compile_to_sexp(program, keyword_to_int)

    def has_unquote(form):
        if form.is_list() and len(form) > 0:
            return form[0].as_int() == UNQUOTE_KEYWORD or any(has_unquote(_) for _ in form[1:])

        return False

    def rewrite_quasiquote(rewrite_f, reduce_f, form):
        if len(form) < 2:
            return form

        if form[1].is_list() and form[1][0].as_int() == UNQUOTE_KEYWORD:
            return form[1][1]

        if has_unquote(form[1]):
            return SExp([LIST_KEYWORD] + [[QUASIQUOTE_KEYWORD, _] for _ in form[1:][0]])
        return SExp([QUOTE_KEYWORD] + list(form[1:]))

    NATIVE_REWRITE_OPERATORS = [
        ("quasiquote", rewrite_quasiquote),
    ]

    native_rewrite_operators = {}
    for kw, f in NATIVE_REWRITE_OPERATORS:
        native_rewrite_operators[keyword_to_int[kw]] = f

    def rewrite(self, form):

        if form.is_bytes():
            return SExp([QUOTE_KEYWORD, form])

        if form.is_var():
            return SExp([GET_RAW_KEYWORD, [ENV_RAW_KEYWORD], [QUOTE_KEYWORD, form.var_index()]])

        if len(form) == 0:
            return SExp([QUOTE_KEYWORD, form])

        first_item = form[0]

        if first_item.is_list():
            new_env = form[1:]
            new_first_item = self(self, first_item)
            new_form = reduce_f(reduce_f, new_first_item, new_env)
            return self(self, new_form)

        if first_item.is_bytes():
            f_index = first_item.as_int()

            if f_index in (QUOTE_KEYWORD, ENV_RAW_KEYWORD):
                return form

            f = native_rewrite_operators.get(f_index)
            if f:
                new_form = f(self, reduce_f, form)
                return self(self, new_form)

            f = derived_operators.get(f_index)
            if f:
                new_form = SExp([f] + list(form[1:]))
                return self(self, new_form)

            args = SExp([self(self, _) for _ in form[1:]])

            if f_index == REDUCE_KEYWORD and len(args) == 1:
                if args[0].is_list():
                    r_first = args[0][0]
                    if r_first.as_int() == QUOTE_KEYWORD:
                        return args[0][1]

            new_form = SExp([first_item] + list(args))

            if reduce_constants:
                new_form = optimize_form(optimize_form, new_form)

            return new_form

        return form

    return rewrite


def make_optimize_form_f(keyword_to_int, reduce_f):

    QUOTE_KEYWORD = keyword_to_int["quote"]
    ENV_RAW_KEYWORD = keyword_to_int["env_raw"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]

    def contains_no_free_variables(form):
        if form.is_list():
            first_item = form[0]
            if first_item.is_list():
                return False
            if first_item == ENV_RAW_KEYWORD:
                return False
            if first_item == QUOTE_KEYWORD:
                return True
            if first_item == REDUCE_KEYWORD:
                if len(form) > 2:
                    return contains_no_free_variables(form[2])
            return all(contains_no_free_variables(_) for _ in form[1:])

        if form.is_var():
            return False

        return True

    def optimize_form(self, form):

        if not form.is_list():
            return form

        if len(form) == 0:
            return SExp([QUOTE_KEYWORD, form])

        first_item = form[0]

        if not first_item.is_bytes():
            return form

        f_index = first_item.as_int()

        if f_index == QUOTE_KEYWORD:
            return form

        args = SExp([self(self, _) for _ in form[1:]])

        new_form = SExp([first_item] + list(args))

        if contains_no_free_variables(new_form):
            empty_env = SExp([])
            new_form = reduce_f(reduce_f, new_form, empty_env)
            return SExp([QUOTE_KEYWORD, new_form])

        return new_form

    return optimize_form


def op_rewrite(items):
    return rewrite_f(rewrite_f, items[0])


# TODO: rewrite as a derived operator
def op_and(items):
    if any(_ == SExp(0) for _ in items):
        return SExp(0)
    return SExp(1)


def make_rewriting_reduce(rewrite_f, core_reduce_f, log_reduce_f):
    def my_reduce_f(self, form, env):
        rewritten_form = rewrite_f(rewrite_f, form)
        rv = core_reduce_f(self, rewritten_form, env)
        log_reduce_f(SExp([form, rewritten_form, env, rv]))
        return rv
    return my_reduce_f


the_log = []
rewrite_f = make_rewrite_f(KEYWORD_TO_INT, core_reduce_f, reduce_constants=False)
do_reduce_f = make_rewriting_reduce(rewrite_f, core_reduce_f, the_log.append)
do_reduce_f.trace_log = the_log

DOMAIN_OPERATORS = (
    ("+", op_add),
    ("-", op_subtract),
    ("*", op_multiply),
    ("sha256", op_sha256),
    ("unwrap", op_unwrap),
    ("wrap", op_wrap),
    ("and", op_and),
    ("rewrite_op", op_rewrite),
)


operator_lookup = OPERATOR_LOOKUP = {KEYWORD_TO_INT[op]: f for op, f in DOMAIN_OPERATORS}

core_reduce_f.operator_lookup.update(operator_lookup)


def transform(sexp):
    pass
