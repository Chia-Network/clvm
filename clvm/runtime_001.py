import io

from opacity.Var import Var
from opacity.int_keyword import to_int_keyword_tokens
from opacity.writer import write_tokens

from . import more_operators

from .casts import int_from_bytes, int_to_bytes
from .corevm_0_0_1 import build_runtime, operators_for_dict, operators_for_module
from .ReduceError import ReduceError
from .RExp import subclass_rexp
from .serialize import make_sexp_from_stream, sexp_to_stream


class mixin:
    @classmethod
    def to_atom(class_, v):
        if isinstance(v, int):
            v = int_to_bytes(v)
        return v

    def as_int(self):
        return int_from_bytes(self.as_atom())

    def as_bin(self):
        f = io.BytesIO()
        sexp_to_stream(self, f)
        return f.getvalue()

    @classmethod
    def from_blob(class_, blob):
        return sexp_from_stream(io.BytesIO(blob))

    def __iter__(self):
        return self.as_iter()

    def __repr__(self):
        tokens = to_int_keyword_tokens(self, KEYWORD_FROM_ATOM)
        return write_tokens(tokens)


to_sexp_f = subclass_rexp(mixin, (bytes, Var))
sexp_from_stream = make_sexp_from_stream(to_sexp_f)

CORE_KEYWORDS = ". quote eval args if cons first rest listp raise eq".split()

CORE_KEYWORDS = ". q e a i c f r l x =".split()

MORE_KEYWORDS = (
    "sha256 + - * . wrap unwrap point_add pubkey_for_exp").split()
KEYWORDS = CORE_KEYWORDS + MORE_KEYWORDS

OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
    "i": "if",
    "c": "cons",
    "f": "first",
    "r": "rest",
    "l": "listp",
    "x": "raise",
    "=": "eq",
}


def op_if(args):
    r = args.rest()
    if args.first().nullp():
        return r.rest().first()
    return r.first()


def op_cons(args):
    return args.first().cons(args.rest().first())


def op_first(args):
    return args.first().first()


def op_rest(args):
    return args.first().rest()


def op_listp(args):
    return args.true if args.first().listp() else args.false


def op_raise(args):
    raise ReduceError(args)


def op_eq(args):
    a0 = args.first()
    a1 = args.rest().first()
    if a0.listp() or a1.listp():
        raise ReduceError("= on list")
    return args.true if a0.as_atom() == a1.as_atom() else args.false


KEYWORD_FROM_ATOM = {int_to_bytes(k): v for k, v in enumerate(KEYWORDS)}
KEYWORD_TO_ATOM = {v: k for k, v in KEYWORD_FROM_ATOM.items()}

OPERATOR_LOOKUP = operators_for_dict(KEYWORD_TO_ATOM, globals(), OP_REWRITE)
OPERATOR_LOOKUP.update(operators_for_module(KEYWORD_TO_ATOM, more_operators, OP_REWRITE))

reduce_f, transform, to_tokens, from_tokens = build_runtime(
    to_sexp_f, KEYWORD_FROM_ATOM, KEYWORD_TO_ATOM, OPERATOR_LOOKUP, CORE_KEYWORDS[1:4])
