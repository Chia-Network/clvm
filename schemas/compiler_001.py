from opacity.casts import int_from_bytes, int_to_bytes
from opacity import core_operators
from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens
from opacity.reader import read_tokens
from opacity.writer import write_tokens
from opacity.RExp import subclass_rexp
from opacity.Var import Var

from .corevm_0_0_1 import operators_for_module, operators_for_dict

from . import more_operators
from . import runtime_001


class mixin:
    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def __iter__(self):
        return self.as_iter()

    def __len__(self):
        return len(list(self.as_iter()))

    def get_sublist_at_index(self, s):
        sexp = self
        while s > 0:
            sexp = sexp.v[1]
            s -= 1
        return sexp

    def get_at_index(self, s):
        return self.get_sublist_at_index(s).v[0]

    def __getitem__(self, s):
        if isinstance(s, int):
            return self.get_at_index(s)
        if s.stop is None and s.step is None:
            return self.get_sublist_at_index(s.start)

    def __repr__(self):
        tokens = to_int_keyword_tokens(self, KEYWORD_FROM_INT)
        return write_tokens(tokens)


to_sexp_f = subclass_rexp(mixin, (bytes, Var))


KEYWORDS = (
    ". quote e args if_op cons first rest listp raise eq_atom "
    "eval if pubkey_for_exp equal sha256 + * - / wrap unwrap list "
    "compile compile_op quasiquote unquote case var not and or map function ").split()


KEYWORD_FROM_INT = {int_to_bytes(k): v for k, v in enumerate(KEYWORDS)}
KEYWORD_TO_INT = {v: k for k, v in KEYWORD_FROM_INT.items()}


DERIVED_OPERATORS = [
    # when we find one of these, do the following:
    #   - macro expand (uses .rest() as args) to remove x0, x1, etc. arguments
    #   - eval as a compiler_001 program (with params to the macro as arguments)
    #   - this should yield another compiler_001 program, which we compile again
    ("compile",
        "(quote (compile_op (quote x0)))"),
    ("eval",
        "(quote (e (compile_op (e (compile_op (quote x0)) (args))) x1))"),
    ("if",
        "(quote (e (if_op x0 (function x1) (function x2)) (args)))"),
    ("list",
        "(if (args) "
        "(cons #cons (cons (first (args)) (cons (cons #list (rest (args))) (quote ())))) "
        "(quote ()))"),
]


DERIVED_OPERATORS_PROGRAMS = {}
for kw, program in DERIVED_OPERATORS:
    DERIVED_OPERATORS_PROGRAMS[KEYWORD_TO_INT[kw]] = to_sexp_f(from_int_keyword_tokens(
        read_tokens(program), KEYWORD_TO_INT))


# TODO: rewrite as a derived operator
def op_and(items):
    if any(_ == items.false for _ in items):
        return items.false
    return items.true


def op_compile_op(items):
    #breakpoint()
    return compile_f(compile_f, items.first())


def macro_expand(sexp, args):
    if sexp.listp():
        return sexp.to([macro_expand(_, args) for _ in sexp])

    atom = sexp.as_atom()
    if isinstance(atom, Var):
        index = atom.index
        while index > 0:
            args = args.rest()
            index -= 1
        return args.first()
    return sexp


eval_f = runtime_001.reduce_f

runtime_001.KEYWORD_TO_ATOM["compile_op"] = KEYWORD_TO_INT["compile_op"]
runtime_001.OPERATOR_LOOKUP[KEYWORD_TO_INT["compile_op"]] = op_compile_op


CORE_REMAP = {
    KEYWORD_TO_INT[_from]: runtime_001.KEYWORD_TO_ATOM[_to] for _from, _to in (
        ("quote", "q"),
        ("args", "a"),
        ("e", "e"),
        ("if_op", "i"),
        ("cons", "c"),
        ("first", "f"),
        ("rest", "r"),
        ("listp", "l"),
        ("raise", "x"),
        ("eq_atom", "="),
        ("+", "+"),
        ("-", "-"),
        ("*", "*"),
        ("compile_op", "compile_op"),
    )
}


def compile_f(compile_f, sexp):
    if sexp.nullp():
        return runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["q"], None])

    if not sexp.listp():
        atom = sexp.as_atom()
        if isinstance(atom, bytes):
            r = runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["q"], atom])
            return r

        if isinstance(atom, Var):
            index = atom.index
            sexp = runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["a"]])
            for _ in range(index):
                sexp = runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["r"], sexp])
            r = runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["f"], sexp])
            return r

    first_item = sexp.first()
    f_index = first_item.as_atom()

    if f_index == KEYWORD_TO_INT["quote"]:
        r = runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["q"], sexp.rest().first()])
        return r

    if f_index == KEYWORD_TO_INT["function"]:
        new_sexp = compile_f(compile_f, sexp.rest().first())
        r = runtime_001.to_sexp_f([runtime_001.KEYWORD_TO_ATOM["q"], new_sexp])
        return r

    if f_index in DERIVED_OPERATORS_PROGRAMS:
        #breakpoint()
        prog = DERIVED_OPERATORS_PROGRAMS[f_index]
        args = sexp.rest()
        expanded_prog = macro_expand(prog, args)
        sexp = compile_f(compile_f, expanded_prog)
        r = runtime_001.reduce_f(runtime_001.reduce_f, sexp, args)
        print("op: %s" % KEYWORD_FROM_INT[f_index])
        print("  args: %s" % args)
        print("  prog: %s" % prog)
        print("  expanded_prog: %s" % expanded_prog)
        print("  sexp: %s" % sexp)
        print("  r: %s" % r)
        return compile_f(compile_f, r)

    args = sexp.to([compile_f(compile_f, _) for _ in sexp.rest().as_iter()])

    if f_index in CORE_REMAP:
        remapped_keyword = CORE_REMAP[f_index]
        r = runtime_001.to_sexp_f(remapped_keyword).cons(args)
        return r

    print("BAD f_index: %s" % f_index)
    print(sexp)
    breakpoint()
    return sexp


MORE_OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "if_op": "if",
}


def debug_compile_f(f, sexp):
    #print("COMPILING: %s" % sexp)
    new_sexp = compile_f(f, sexp)
    print("COMPILED: %s\n %s" % (sexp, new_sexp))
    return new_sexp


def my_eval_f(my_eval_f, sexp, args):
    print("EVAL %s" % sexp)
    new_sexp = debug_compile_f(debug_compile_f, sexp)
    return runtime_001.reduce_f(runtime_001.reduce_f, new_sexp, args)


def transform(sexp):
    if sexp.listp():
        if sexp.nullp():
            return sexp
        sexp, args = sexp.first(), sexp.rest()
    else:
        args = sexp.null

    return my_eval_f(my_eval_f, sexp, args)


def to_tokens(sexp):
    return to_int_keyword_tokens(sexp, KEYWORD_FROM_INT)


def from_tokens(sexp):
    return to_sexp_f(from_int_keyword_tokens(sexp, KEYWORD_TO_INT))


def from_stream(f):
    return sexp_from_stream(f)
