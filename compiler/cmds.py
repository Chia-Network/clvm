import argparse
import binascii
import sys

from .reader import read_tokens
from opacity.writer import write_tokens

from clvm import core_ops, more_ops
from clvm.make_eval import make_eval_f, EvalError
from clvm.op_utils import operators_for_module, operators_for_dict


class CompileError(ValueError):
    pass


QUOTE_KEYWORD = "q"
EVAL_KEYWORD = "e"
ARGS_KEYWORD = "a"
CONS_KEYWORD = "c"
LIST_KEYWORD = "list"


def arg_index(index):
    """
    Generate code that drills down to correct args node
    """
    if index == 0:
        return [ARGS_KEYWORD]
    return ["f" if index & 1 else "r", arg_index((index-1) >> 1)]


def do_local_subsitution(sexp, arg_lookup):
    if sexp.listp():
        if not sexp.nullp() and sexp.first().as_atom() == "quote":
            return sexp
        return sexp.to([sexp.first()] + [
            do_local_subsitution(_, arg_lookup) for _ in sexp.rest().as_iter()])
    b = sexp.as_atom()
    return sexp.to(arg_index(arg_lookup.get(b)))


def parse_defun(dec):
    name, args, definition = list(dec.rest().as_iter())

    # do arg substitution in definition so it's in terms of indices
    arg_lookup = {_.as_atom(): (4 << index) - 3 for index, _ in enumerate(args.as_iter())}

    def builder(compile_sexp, args, function_rewriters, function_index_lookup):
        args = args.to([compile_sexp(
            compile_sexp, _, function_rewriters, function_index_lookup) for _ in args.as_iter()])
        function_index = function_index_lookup[name.as_atom()]
        return args.to([EVAL_KEYWORD, arg_index(function_index), [
            CONS_KEYWORD, arg_index(0), [LIST_KEYWORD] + list(args.as_iter())]])

    imp = do_local_subsitution(definition, arg_lookup)

    return name.as_atom(), builder, imp


def parse_defmacro(dec):
    name, args, definition = list(dec.rest().as_iter())

    arg_lookup = {_.as_atom(): index for index, _ in enumerate(args.as_iter())}

    def builder(compile_sexp, args, function_rewriters, function_index_lookup):
        args = list(args.as_iter())
        # substitute in variables
        arg_replacement = {k: args[v] for k, v in arg_lookup.items()}
        new_sexp = macro_expand(definition, arg_replacement)
        # run it
        r = eval_f(eval_f, new_sexp, args)
        # compile the output and return that
        return compile_sexp(compile_sexp, r, function_rewriters, function_index_lookup)

    imp = None

    return name.as_atom(), builder, imp


def parse_declaration(declaration):
    if declaration.first() == "defun":
        return parse_defun(declaration)
    if declaration.first() == "defmacro":
        return parse_defmacro(declaration)
    raise SyntaxError("only defun and defmacro expected here")


def make_remap(keyword, compiled_keyword):
    def remap(compile_sexp, args, function_rewriters, function_index_lookup):
        return args.to([compiled_keyword] + list(compile_sexp(
            compile_sexp, _, function_rewriters, function_index_lookup) for _ in args.as_iter()))
    return remap


def remap_eval(compile_sexp, sexp, function_rewriters, function_index_lookup):
    args = sexp.to([compile_sexp(compile_sexp, _, function_rewriters, function_index_lookup) for _ in sexp])
    r1 = sexp.to([EVAL_KEYWORD, args.first(), [ARGS_KEYWORD]])
    return r1


def remap_function(compile_sexp, sexp, function_rewriters, function_index_lookup):
    args = sexp.to([compile_sexp(compile_sexp, _, function_rewriters, function_index_lookup) for _ in sexp])
    r1 = sexp.to([QUOTE_KEYWORD, args.first()])
    return r1


def get_built_in_functions():
    REMAP_LIST = {
        "+": "+",
        "cons": "c",
        "first": "f",
        "rest": "r",
        "args": "a",
    }
    remapped = {k: make_remap(k, v) for k, v in REMAP_LIST.items()}
    remapped["eval"] = remap_eval
    remapped["function"] = remap_function
    return remapped


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def parse_as_int(sexp):
    try:
        int(sexp.as_atom())
        return sexp.to([QUOTE_KEYWORD, sexp])
    except (ValueError, TypeError):
        pass


def parse_as_hex(sexp):
    token = sexp.as_atom()
    if token[:2].upper() == "0X":
        try:
            return sexp.to(bytes_as_hex(binascii.unhexlify(token[2:])))
        except Exception:
            raise SyntaxError("invalid hex at %d: %s" % (token._offset, token))


def parse_as_var(sexp):
    token = sexp.as_atom()
    if token[:1].upper() == "X":
        try:
            index = int(token[1:])
            return sexp.to(arg_index(index))
        except Exception:
            raise SyntaxError("invalid variable at %d: %s" % (token._offset, token))


def compile_atom(sexp):
    token = sexp.as_atom()
    c = token[0]
    if c in "\'\"":
        assert c == token[-1] and len(token) >= 2
        return sexp.to(["q", token])

    for f in [parse_as_int, parse_as_var, parse_as_hex]:
        v = f(sexp)
        if v is not None:
            return v
    raise SyntaxError("can't parse %s at %d" % (token, token._offset))


def compile_sexp(self, sexp, function_rewriters, function_index_lookup):
    # x0: function table
    # x1, x2...: env
    # (function_x a b c ...) => (reduce (get_raw x0 #function_x) (list x0 a b c))
    if not sexp.listp():
        r = compile_atom(sexp)
        return r
    opcode = sexp.first().as_atom()
    if opcode == "quote":
        if sexp.rest().nullp() or not sexp.rest().rest().nullp():
            raise SyntaxError("quote requires 1 argument, got %s" % sexp.rest())
        return sexp.to(["q", sexp.rest().first()])
    if opcode in function_rewriters:
        return function_rewriters[opcode](self, sexp.rest(), function_rewriters, function_index_lookup)
    raise SyntaxError("unknown keyword %s" % opcode)


def macro_expand(definition, arg_lookup):
    if definition.listp():
        if definition.nullp():
            raise SyntaxError("definition is null")
        t1 = [macro_expand(_, arg_lookup) for _ in definition.rest().as_iter()]
        t2 = [definition.first()]
        t3 = t2 + t1
        return definition.to(t3)

    as_atom = definition.as_atom()
    if as_atom in arg_lookup:
        return arg_lookup[as_atom]
    return definition


def rename_vars(defun):
    (name, arg_lookup, definition) = defun
    return macro_expand(definition, arg_lookup)


def rewrite_defun(compile_sexp, defun, function_rewriters, function_index_lookup):
    # (name, arg_lookup, definition) = defun
    sexp = rename_vars(defun)
    return compile_sexp(compile_sexp, sexp, function_rewriters, function_index_lookup)


def build_function_table(compile_sexp, defuns, function_rewriters, function_index_lookup):
    table = []
    for defun in defuns:
        table.append(rewrite_defun(compile_sexp, defun, function_rewriters, function_index_lookup))
    return table


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


def op_prog(sexp):
    function_rewriters = get_built_in_functions()
    local_function_rewriters = {}
    function_imps = {}
    function_name_lookup = []
    for declaration in sexp.first().as_iter():
        name, builder, imp = parse_declaration(declaration)
        local_function_rewriters[name] = builder
        if imp is not None:
            function_imps[name] = imp
            function_name_lookup.append(name)
    # build the function table and put that in x0
    function_index_lookup = {v: (4 << k) - 3 for k, v in enumerate(function_name_lookup)}
    function_table = []
    function_rewriters.update(local_function_rewriters)
    function_table = [
        compile_sexp(compile_sexp, function_imps[name], function_rewriters, function_index_lookup)
        for name in function_name_lookup]
    r = compile_sexp(compile_sexp, sexp.rest().first(), function_rewriters, function_index_lookup)
    r1 = sexp.to([EVAL_KEYWORD, [QUOTE_KEYWORD, r], [
        CONS_KEYWORD, [QUOTE_KEYWORD, function_table], [ARGS_KEYWORD]]])
    return r1


KEYWORDS = (
    ". quote eval args if cons first rest listp raise eq sha256 "
    "+ - * . wrap unwrap point_add pubkey_for_exp prog ".split())

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


eval_list_f = make_eval_f(operators, "quote", "eval", "args")


def eval_f(self, sexp, args):
    print("SEXP: %s [%s]" % (sexp, args))
    if sexp.nullp():
        return sexp

    if sexp.listp():
        return eval_list_f(eval_f, sexp, args)

    return sexp


def do_eval(sexp):
    return eval_f(eval_f, sexp, sexp.null())


def path_or_code(arg):
    try:
        with open(arg) as f:
            return f.read()
    except IOError:
        return arg


def run(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )
    parser.add_argument(
        "path_or_code", type=path_or_code, help="path to opacity script, or literal script")
    parser.add_argument("-r", "--reduce", help="Run compiled code")

    args = parser.parse_args(args=args[1:])

    prog = args.path_or_code
    sexp = read_tokens(prog)
    try:
        result = do_eval(sexp)
    except EvalError as ex:
        print("FAILURE: %s" % ex)
        result = ex._sexp
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
