import argparse
import hashlib
import sys

from opacity.writer import write_tokens

from clvm import core_ops, more_ops
from clvm.make_eval import make_eval_f, EvalError
from clvm.op_utils import operators_for_module, operators_for_dict

from .compile import op_compile_op
from .expand import op_expand_op, op_expand_sexp
from .prog import op_prog_op
from .reader import read_tokens


def has_unquote(sexp):
    if sexp.listp():
        if not sexp.rest().nullp():
            if sexp.rest().first() == "unquote":
                return True
            return any(has_unquote(_) for _ in sexp.rest().as_list())
    return False


def macro_quasiquote(sexp):
    if sexp.rest().nullp() or not sexp.rest().rest().nullp():
        raise EvalError("quasiquote requires exactly 1 parameter", sexp)

    item = sexp.rest().first()
    if item.listp() and item.as_atom() == "unquote":
        return item.rest().first()

    if has_unquote(item):
        return sexp.to(["list"] + [macro_quasiquote(_) for _ in item.rest()])
    return sexp.to(["quote", item])


#########################


def op_equal(sexp):
    while not sexp.nullp() and not sexp.rest().nullp():
        o1, o2 = sexp.first(), sexp.rest().first()
        if o1.as_atom() != o2.as_atom():
            return sexp.false
        sexp = sexp.rest()

    return sexp.true


def op_sha256(args):
    h = hashlib.sha256()
    for _ in args.as_iter():
        h.update(_.as_bytes())
    return args.to("0x%s" % h.hexdigest())


def op_if_op(args):
    r = args
    if r.first().nullp():
        r = r.rest()
    return r.rest().first()


def op_function_op(args):
    return args.to(["compile", args.first()])


def op_call(args):
    if args.listp() and not args.nullp():
        arg0 = args.first()
        if arg0.listp() and not args.nullp():
            if arg0.first().as_atom() == "compile":
                return do_eval(arg0.rest().first(), args.rest().first())
    raise EvalError("call only works on compiled code", args)


KEYWORDS = (
    ". quote eval args if cons first rest listp raise eq sha256 "
    "+ - * . wrap unwrap point_add pubkey_for_exp equal "
    "and list expand expand_op compile compile_op prog prog_op if_op function call ".split())

KEYWORD_MAP = {k: k for k in KEYWORDS}

OP_REWRITE = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
}

operators = operators_for_module(KEYWORD_MAP, core_ops, OP_REWRITE)
operators.update(operators_for_module(KEYWORD_MAP, more_ops, OP_REWRITE))
operators.update(operators_for_dict(KEYWORD_MAP, globals(), OP_REWRITE))
operators["compile_op"] = op_compile_op
operators["expand_op"] = op_expand_op
operators["function_op"] = op_function_op
operators["prog_op"] = op_prog_op
operators["call"] = op_call


eval_list_f = make_eval_f(operators, "quote", "eval", "args")


def eval_f(self, sexp, args):
    sexp = op_expand_sexp(sexp)
    return eval_list_f(eval_f, sexp, args)


def do_eval(sexp, args):
    return eval_f(eval_f, sexp, args)


def path_or_code(arg):
    try:
        with open(arg) as f:
            return f.read()
    except IOError:
        return arg


def arguments(s):
    return read_tokens(s)


def run(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )
    parser.add_argument(
        "path_or_code", type=path_or_code, help="path to opacity script, or literal script")
    parser.add_argument(
        "args", type=arguments, help="arguments", nargs="?", default=read_tokens("()"))
    parser.add_argument("-r", "--reduce", help="Run compiled code")

    args = parser.parse_args(args=args[1:])

    prog = args.path_or_code
    sexp = read_tokens(prog)
    try:
        result = do_eval(sexp, args.args)
    except EvalError as ex:
        print("FAILURE: %s" % ex)
        result = ex._sexp
        # raise
    finally:
        print(write_tokens(result))


"""
Copyright 2019 Chia Network Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
