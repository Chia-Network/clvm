import argparse
import collections
import sys

from opacity.compile import tokenize_program, disassemble
from opacity.keywords import KEYWORD_TO_INT, KEYWORD_FROM_INT
from opacity.SExp import SExp


QUOTE_KEYWORD = KEYWORD_TO_INT["quote"]


Context = collections.namedtuple("Context", "defuns defmacros op_lookup".split())


def parse_defun(dec, context):
    name, args, definition = dec[1:]
    # do arg substitution in definition so it's in terms of x1, x2, etc.
    arg_lookup = {var: index+1 for index, var in enumerate(args)}
    context.defuns.append((name, arg_lookup, definition))


def parse_defmacro(dec, context):
    raise ValueError("not implemented")


def parse_declaration(declaration, context):
    if declaration[0] == "defun":
        return parse_defun(declaration, context)
    if declaration[0] == "demacro":
        return parse_defmacro(declaration, context)
    raise ValueError("foo")


def to_sexp(sexp):
    if isinstance(sexp, SExp):
        return sexp
    if isinstance(sexp, str):
        return sexp.encode("utf8")
    return SExp([to_sexp(_) for _ in sexp])


def make_remap(keyword, keyword_to_int):
    keyword_v = keyword_to_int[keyword]

    def remap(compile_exp, sexp, built_in_functions, function_name_lookup):
        args = SExp([compile_exp(compile_exp, _, built_in_functions, function_name_lookup) for _ in sexp])
        return SExp([keyword_v] + list(args))
    return remap


def get_built_in_functions():
    REMAP_LIST = "quote get + * get_raw env_raw".split()
    remapped = {k: make_remap(k, KEYWORD_TO_INT) for k in REMAP_LIST}
    return remapped


REDUCE_KEYWORD = KEYWORD_TO_INT["reduce"]
GET_RAW_KEYWORD = KEYWORD_TO_INT["get_raw"]
ENV_RAW_KEYWORD = KEYWORD_TO_INT["env_raw"]
LIST_KEYWORD = KEYWORD_TO_INT["list"]
CONS_KEYWORD = KEYWORD_TO_INT["cons"]


def compile_exp(self, sexp, built_in_functions, function_name_lookup):
    # x0: function table
    # x1, x2...: env
    # (function_x a b c ...) => (reduce (get_raw x0 #function_x) (list x0 a b c))
    if isinstance(sexp, str):
        return sexp.encode("utf8")
    if isinstance(sexp, int):
        return SExp(sexp)
    opcode = sexp[0]
    if opcode in built_in_functions:
        return built_in_functions[opcode](self, sexp[1:], built_in_functions, function_name_lookup)
    args = SExp([compile_exp(self, _, built_in_functions, function_name_lookup) for _ in sexp[1:]])
    if opcode in function_name_lookup:
        opcode_index = function_name_lookup[opcode]
        return SExp([REDUCE_KEYWORD, [GET_RAW_KEYWORD, [
            GET_RAW_KEYWORD, [ENV_RAW_KEYWORD], 0], opcode_index], [
            CONS_KEYWORD, [GET_RAW_KEYWORD, [ENV_RAW_KEYWORD], 0], [LIST_KEYWORD] + list(args)]])
    raise ValueError("unknown keyword %s" % opcode)


def macro_expand(definition, arg_lookup):
    if isinstance(definition, str):
        return ["get_raw", ["env_raw"], arg_lookup[definition]]
    return [definition[0]] + [macro_expand(_, arg_lookup) for _ in definition[1:]]


def rename_vars(defun):
    (name, arg_lookup, definition) = defun
    return macro_expand(definition, arg_lookup)


def rewrite_defun(compile_exp, defun, built_in_functions, function_name_lookup):
    (name, arg_lookup, definition) = defun
    renamed_vars = rename_vars(defun)
    sexp = renamed_vars
    return compile_exp(compile_exp, sexp, built_in_functions, function_name_lookup)


def build_function_table(compile_exp, defuns, built_in_functions, function_name_lookup):
    table = []
    for defun in defuns:
        table.append(rewrite_defun(compile_exp, defun, built_in_functions, function_name_lookup))
    return table


def do_compile(prog):
    context = Context(defuns=[], defmacros=[], op_lookup={})
    tokens = tokenize_program(prog)
    for declaration in tokens[:-1]:
        parse_declaration(declaration, context)
    # build the function table and put that in x0
    built_in_functions = get_built_in_functions()
    function_name_lookup = {defun[0]: index for index, defun in enumerate(context.defuns)}
    function_table = build_function_table(
        compile_exp, context.defuns, built_in_functions, function_name_lookup)
    r = compile_exp(compile_exp, tokens[-1], built_in_functions, function_name_lookup)
    r1 = SExp([REDUCE_KEYWORD, [QUOTE_KEYWORD, r], [
        CONS_KEYWORD, [QUOTE_KEYWORD, function_table], [ENV_RAW_KEYWORD]]])
    return r1


def run(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )

    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    prog = open(args.script).read()
    result = do_compile(prog)
    print(disassemble(result, KEYWORD_FROM_INT))


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
