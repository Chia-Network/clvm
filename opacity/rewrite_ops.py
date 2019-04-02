from .SExp import SExp

from .compile import compile_to_sexp
from .keywords import KEYWORD_TO_INT

ENV_RAW_KEYWORD = KEYWORD_TO_INT["env_raw"]
GET_RAW_KEYWORD = KEYWORD_TO_INT["get"]
QUOTE_KEYWORD = KEYWORD_TO_INT["quote"]
UNQUOTE_KEYWORD = KEYWORD_TO_INT["unquote"]
QUASIQUOTE_KEYWORD = KEYWORD_TO_INT["quasiquote"]
LIST_KEYWORD = KEYWORD_TO_INT["list"]


DERIVED_OPS = [
    ("if", "(quasiquote (reduce (get_default (quote (unquote (list x2))) (unquote (list x1)) (unquote x0))))"),
    ("list",
        "(if (is_null (env_raw)) (quote ()) "
        "(quasiquote (cons (unquote (first (env_raw))) (unquote (cons #list (rest (env_raw)))))))"),
    ("map",
        "(quasiquote (reduce (quote (if (is_null x1) (quote ()) (cons (reduce x0 (list (first x1))) (map x0 (rest x1))))) (quote (unquote (list x0 x1)))))"),

    # need tests for the below
    ("bool",
        "(quasiquote (get_default (quote (0)) (quote 1) (unquote x0)))"),
    ("not",
        "(quasiquote (get_default (quote (1)) (quote 0) (unquote x0)))"),
    ("choose1",
        "(cons #reduce (cons (list #get (cons #quote (cons (rest (env)))) x0)))"),
    ("env",
        "(cons #get (cons (cons #env_raw) (env_raw)))"),
    ("is_atom",
        "(quasiquote (not (equal (type (unquote (quote x0))) 2)))"),
    ("get",
        "(reduce (get_raw "
        "(quote ((cons #get (cons (list #get_raw x0 x1) (rest (rest (env_raw))))) x0)) "
        "(is_null (rest (env_raw)))))"),

]


def make_rewrite(program):
    sexp = compile_to_sexp(program)

    def f(rewrite_f, reduce_f, form, derived_operators):
        return SExp([sexp] + list(form[1:]))

    return f


def has_unquote(form):
    if form.is_list() and len(form) > 0:
        return form[0].as_int() == UNQUOTE_KEYWORD or any(has_unquote(_) for _ in form[1:])

    return False


def rewrite_quasiquote(rewrite_f, reduce_f, form, derived_operators):
    if len(form) < 2:
        return form

    if form[1].is_list() and form[1][0].as_int() == UNQUOTE_KEYWORD:
        return form[1][1]

    if has_unquote(form[1]):
        return SExp([LIST_KEYWORD] + [[QUASIQUOTE_KEYWORD, _] for _ in form[1:][0]])
    return SExp([QUOTE_KEYWORD] + list(form[1:]))


def derived_operators():
    d = {}
    for k, s in DERIVED_OPS:
        d[KEYWORD_TO_INT[k]] = make_rewrite(s)

    d[KEYWORD_TO_INT["quasiquote"]] = rewrite_quasiquote

    return d
