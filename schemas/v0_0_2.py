from opacity.core import make_reduce_f
from opacity import core_operators
from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens
from opacity.reader import read_tokens
from opacity.SExp import SExp


from . import more_operators


KEYWORDS = (
    ". quote aggsig point_add assert_output pubkey_for_exp and type equal "
    "sha256 reduce + * - / wrap unwrap list choose1 quasiquote unquote get env "
    "case is_atom list1 "
    "cons first rest list type is_null var apply eval envr getr "
    "if not bool or map raise rewrite rewrite_op ").split()


KEYWORD_FROM_INT = KEYWORDS
KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}


def operators_for_module(keyword_to_int, mod, op_name_lookup={}):
    d = {}
    for op in keyword_to_int.keys():
        op_name = "op_%s" % op_name_lookup.get(op, op)
        op_f = getattr(mod, op_name, None)
        if op_f:
            d[keyword_to_int[op]] = op_f
    return d


DERIVED_OPERATORS = [
    ("if",
        "(cons (quote #reduce) (cons (cons (quote #get) (cons (cons (quote #quote) "
        "(cons (rest (env)) (quote ()))) (cons (cons (quote #equal) (cons (get "
        "(env) (quote 0)) (quote ((quote 0))))) (quote ())))) (quote ((env)))))"),
    ("list",
        "(if (is_null (env)) "
        "(quote (quote ())) "
        "(cons (quote #cons) (cons (first (env)) "
        "(cons (cons (quote #list) (rest (env))) (quote ())))))"),
    ("bool", "(quasiquote (if (unquote x0) (quote 1) (quote 0)))"),
    ("not", "(quasiquote (if (unquote x0) (quote 0) (quote 1)))"),
    ("choose1",
        "(list #reduce (list #get (cons #quote (list (rest (env)))) x0) (quote (env)))"),
    ("envr",
        "(cons #getr (cons (cons #env (quote ())) (env)))"),
    ("getr",
        "(reduce (get "
        "(quote ((cons (quote #getr) "
        "(cons (cons (quote #get) (cons (get (env) (quote 0)) "
        "(cons (get (env) (quote 1)) (quote ())))) "
        "(rest (rest (env))))) (get (env) (quote 0)))) "
        "(is_null (rest (env)))) (env))"),
    ("map",
        "(quasiquote (reduce (quote (if (is_null x1) (quote ())"
        " (cons (reduce x0 (list (first x1))) (map x0 (rest x1))))) (list (unquote x0) (unquote x1))))"),
    ("assert_output", "(quasiquote (quote (unquote (cons #assert_output (env)))))"),
    ("rewrite", "(quasiquote (rewrite_op (quote (unquote x0))))"),
]


def make_rewrite_f(keyword_to_int, reduce_f, reduce_constants=True):

    ENV_KEYWORD = keyword_to_int["env"]
    GET_KEYWORD = keyword_to_int["get"]
    LIST_KEYWORD = keyword_to_int["list"]
    QUASIQUOTE_KEYWORD = keyword_to_int["quasiquote"]
    QUOTE_KEYWORD = keyword_to_int["quote"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]
    UNQUOTE_KEYWORD = keyword_to_int["unquote"]

    optimize_form = make_optimize_form_f(keyword_to_int, reduce_f)

    derived_operators = {}
    for kw, program in DERIVED_OPERATORS:
        derived_operators[keyword_to_int[kw]] = from_int_keyword_tokens(
            read_tokens(program), keyword_to_int)

    def has_unquote(form):
        if form.listp() and len(form) > 0:
            return form[0].as_int() == UNQUOTE_KEYWORD or any(has_unquote(_) for _ in form[1:])

        return False

    def rewrite_quasiquote(rewrite_f, reduce_f, form):
        if len(form) < 2:
            return form

        if form[1].listp() and form[1][0].as_int() == UNQUOTE_KEYWORD:
            return form[1][1]

        if has_unquote(form[1]):
            return form.__class__([LIST_KEYWORD] + [[QUASIQUOTE_KEYWORD, _] for _ in form[1:][0]])
        return form.__class__([QUOTE_KEYWORD] + list(form[1:]))

    NATIVE_REWRITE_OPERATORS = [
        ("quasiquote", rewrite_quasiquote),
    ]

    native_rewrite_operators = {}
    for kw, f in NATIVE_REWRITE_OPERATORS:
        native_rewrite_operators[keyword_to_int[kw]] = f

    def rewrite(self, form):

        if form.is_bytes():
            return form.__class__([QUOTE_KEYWORD, form])

        if form.is_var():
            return form.__class__([GET_KEYWORD, [ENV_KEYWORD], [QUOTE_KEYWORD, form.var_index()]])

        if len(form) == 0:
            return form.__class__([QUOTE_KEYWORD, form])

        first_item = form[0]

        if first_item.listp():
            new_env = form[1:]
            new_first_item = self(self, first_item)
            new_form = reduce_f(reduce_f, new_first_item, new_env)
            return self(self, new_form)

        if first_item.is_bytes():
            f_index = first_item.as_int()

            if f_index in (QUOTE_KEYWORD, ENV_KEYWORD):
                return form

            f = native_rewrite_operators.get(f_index)
            if f:
                new_form = f(self, reduce_f, form)
                return self(self, new_form)

            f = derived_operators.get(f_index)
            if f:
                new_form = form.__class__([f] + list(form[1:]))
                return self(self, new_form)

            args = form.__class__([self(self, _) for _ in form[1:]])

            if f_index == REDUCE_KEYWORD and len(args) == 1:
                if args[0].listp():
                    r_first = args[0][0]
                    if r_first.as_int() == QUOTE_KEYWORD:
                        return args[0][1]

            new_form = form.__class__([first_item] + list(args))

            if reduce_constants:
                new_form = optimize_form(optimize_form, new_form)

            return new_form

        return form

    return rewrite


def make_optimize_form_f(keyword_to_int, reduce_f):

    QUOTE_KEYWORD = keyword_to_int["quote"]
    ENV_KEYWORD = keyword_to_int["env"]
    REDUCE_KEYWORD = keyword_to_int["reduce"]

    def contains_no_free_variables(form):
        if form.listp():
            first_item = form[0]
            if first_item.listp():
                return False
            if first_item == ENV_KEYWORD:
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

        if not form.listp():
            return form

        if len(form) == 0:
            return form.__class__([QUOTE_KEYWORD, form])

        first_item = form[0]

        if not first_item.is_bytes():
            return form

        f_index = first_item.as_int()

        if f_index == QUOTE_KEYWORD:
            return form

        args = form.__class__([self(self, _) for _ in form[1:]])

        new_form = form.__class__([first_item] + list(args))

        if contains_no_free_variables(new_form):
            empty_env = form.null
            new_form = reduce_f(reduce_f, new_form, empty_env)
            return form.__class__([QUOTE_KEYWORD, new_form])

        return new_form

    return optimize_form


def op_rewrite(items):
    return rewrite_f(rewrite_f, items[0])


# TODO: rewrite as a derived operator
def op_and(items):
    if any(_ == items.__class__(0) for _ in items):
        return items.__class__(0)
    return items.__class__(1)


def make_rewriting_reduce(rewrite_f, core_reduce_f, log_reduce_f):
    def my_reduce_f(self, form, env):
        rewritten_form = rewrite_f(rewrite_f, form)
        rv = core_reduce_f(self, rewritten_form, env)
        log_reduce_f(form.__class__([form, rewritten_form, env, rv]))
        return rv
    return my_reduce_f


MORE_OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
}

OPERATOR_LOOKUP = operators_for_module(KEYWORD_TO_INT, core_operators)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_INT, more_operators, MORE_OP_REWRITE))
OPERATOR_LOOKUP[KEYWORD_TO_INT["and"]] = op_and
OPERATOR_LOOKUP[KEYWORD_TO_INT["rewrite_op"]] = op_rewrite

BASE_REDUCE_F = make_reduce_f(OPERATOR_LOOKUP, KEYWORD_TO_INT)


def reduce_f(self, sexp, args):
    new_sexp = rewrite_f(rewrite_f, sexp)
    return BASE_REDUCE_F(self, new_sexp, args)


rewrite_f = make_rewrite_f(KEYWORD_TO_INT, reduce_f, reduce_constants=False)


def transform(sexp):
    if sexp.listp():
        if len(sexp) == 0:
            return sexp
        sexp, args = sexp[0], sexp[1:]
    else:
        args = sexp.null

    return reduce_f(reduce_f, sexp, args)


def to_tokens(sexp):
    return to_int_keyword_tokens(sexp, KEYWORD_FROM_INT)


def from_tokens(sexp):
    return from_int_keyword_tokens(sexp, KEYWORD_TO_INT)


def from_stream(f):
    return SExp.from_stream(f)
