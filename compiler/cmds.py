import argparse
import binascii
import collections
import sys

from opacity.keywords import KEYWORD_TO_INT, KEYWORD_FROM_INT
from opacity.SExp import SExp, ATOM_TYPES

from .reader import tokenize_program
from .writer import disassemble


class CompileError(ValueError):
    pass


QUOTE_KEYWORD = KEYWORD_TO_INT["quote"]
REDUCE_KEYWORD = KEYWORD_TO_INT["reduce"]
ENV_KEYWORD = KEYWORD_TO_INT["env"]
LIST_KEYWORD = KEYWORD_TO_INT["list"]
CONS_KEYWORD = KEYWORD_TO_INT["cons"]


Context = collections.namedtuple("Context", "defuns defmacros op_lookup".split())


def do_local_subsitution(sexp, arg_lookup):
    if sexp.type == ATOM_TYPES.BLOB:
        b = sexp.as_bytes()
        return arg_lookup.get(b, b)
    if sexp.type == ATOM_TYPES.PAIR:
        if len(sexp) > 1 and sexp[0].as_bytes() == b"quote":
            return sexp
        return SExp([do_local_subsitution(_, arg_lookup) for _ in sexp])
    assert 0


def parse_defun(dec):
    name, args, definition = dec[1:]
    # do arg substitution in definition so it's in terms of x1, x2, etc.
    arg_lookup = {var.as_bytes(): b"x%d" % (index+1) for index, var in enumerate(args)}

    def builder(compile_sexp, sexp, function_rewriters, function_index_lookup):
        args = [compile_sexp(
            compile_sexp, _, function_rewriters, function_index_lookup) for _ in sexp]
        function_index = function_index_lookup[name.as_bytes()]
        return SExp([REDUCE_KEYWORD, [ENV_KEYWORD, 0, function_index], [
            CONS_KEYWORD, [ENV_KEYWORD, 0], [LIST_KEYWORD] + list(args)]])

    imp = do_local_subsitution(definition, arg_lookup)

    return name.as_bytes(), builder, imp


def parse_defmacro(dec, context):
    raise ValueError("not implemented")


def parse_declaration(declaration):
    if declaration[0] == b"defun":
        return parse_defun(declaration)
    if declaration[0] == b"demacro":
        return parse_defmacro(declaration)
    raise ValueError("foo")


def to_sexp(sexp):
    if isinstance(sexp, SExp):
        return sexp
    return SExp([to_sexp(_) for _ in sexp])


def make_remap(keyword, keyword_to_int):
    keyword_v = keyword_to_int[keyword]

    def remap(compile_sexp, sexp, function_rewriters, function_index_lookup):
        args = SExp([compile_sexp(compile_sexp, _, function_rewriters, function_index_lookup) for _ in sexp])
        return SExp([keyword_v] + list(args))
    return remap


def remap_eval(compile_sexp, sexp, function_rewriters, function_index_lookup):
    args = SExp([compile_sexp(compile_sexp, _, function_rewriters, function_index_lookup) for _ in sexp])
    r1 = SExp([REDUCE_KEYWORD, args[0], [ENV_KEYWORD]])
    return r1


def remap_function(compile_sexp, sexp, function_rewriters, function_index_lookup):
    args = SExp([compile_sexp(compile_sexp, _, function_rewriters, function_index_lookup) for _ in sexp])
    r1 = SExp([QUOTE_KEYWORD, args[0]])
    return r1


def get_built_in_functions():
    REMAP_LIST = "quote get + - * equal list get_raw env_raw".split()
    remapped = {k.encode("utf8"): make_remap(k, KEYWORD_TO_INT) for k in REMAP_LIST}
    remapped[b"eval"] = remap_eval
    remapped[b"function"] = remap_function
    return remapped


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def parse_as_int(token):
    try:
        v = int(token)
        return SExp(v)
    except (ValueError, TypeError):
        pass


def parse_as_hex(token):
    if token[:2].upper() == "0X":
        try:
            return SExp(bytes_as_hex(binascii.unhexlify(token[2:])))
        except Exception:
            raise SyntaxError("invalid hex at %d: %s" % (token._offset, token))


def parse_as_var(token):
    if token[:1].upper() == "X":
        try:
            return SExp.from_var_index(int(token[1:]))
        except Exception:
            raise SyntaxError("invalid variable at %d: %s" % (token._offset, token))


def compile_atom(token, keyword_to_int):
    c = token[0]
    if c in "\'\"":
        assert c == token[-1] and len(token) >= 2
        return SExp(token[1:-1].encode("utf8"))

    if c == '#':
        keyword = token[1:].lower()
        keyword_id = keyword_to_int.get(keyword)
        if keyword_id is None:
            raise SyntaxError("unknown keyword: %s" % keyword)
        return SExp(keyword_id)

    for f in [parse_as_int, parse_as_var, parse_as_hex]:
        v = f(token)
        if v is not None:
            return v
    raise SyntaxError("can't parse %s at %d" % (token, token._offset))


def compile_sexp(self, sexp, function_rewriters, function_index_lookup):
    # x0: function table
    # x1, x2...: env
    # (function_x a b c ...) => (reduce (get_raw x0 #function_x) (list x0 a b c))
    if sexp.type == ATOM_TYPES.BLOB:
        r = compile_atom(sexp.as_bytes().decode("utf8"), KEYWORD_TO_INT)
        if r.is_var():
            r = SExp([ENV_KEYWORD, r.var_index()])
        return r
    opcode = sexp[0].as_bytes()
    if opcode in function_rewriters:
        return function_rewriters[opcode](self, sexp[1:], function_rewriters, function_index_lookup)
    raise ValueError("unknown keyword %s" % opcode)

    args = SExp([compile_sexp(self, _, function_rewriters, function_index_lookup) for _ in sexp[1:]])
    if opcode in function_index_lookup:
        opcode_index = function_index_lookup[opcode]
        return SExp([REDUCE_KEYWORD, [ENV_KEYWORD, 0, opcode_index], [
            CONS_KEYWORD, [ENV_KEYWORD, 0], [LIST_KEYWORD] + list(args)]])


def macro_expand(definition, arg_lookup):
    if definition.type == ATOM_TYPES.BLOB:
        if definition.as_bytes() in arg_lookup:
            return SExp([b"get_raw", [b"env_raw"], arg_lookup[definition.as_bytes()]])
        assert 0
    if definition.type == ATOM_TYPES.PAIR:
        t1 = [macro_expand(_, arg_lookup) for _ in definition[1:]]
        t2 = [definition[0]]
        t3 = t2 + t1
        return SExp(t3)


def rename_vars(defun):
    (name, arg_lookup, definition) = defun
    t = SExp(definition)
    return macro_expand(t, arg_lookup)


def rewrite_defun(compile_sexp, defun, function_rewriters, function_index_lookup):
    #(name, arg_lookup, definition) = defun
    sexp = rename_vars(defun)
    return compile_sexp(compile_sexp, sexp, function_rewriters, function_index_lookup)


def build_function_table(compile_sexp, defuns, function_rewriters, function_index_lookup):
    table = []
    for defun in defuns:
        table.append(rewrite_defun(compile_sexp, defun, function_rewriters, function_index_lookup))
    return table


def convert_list_of_lists_to_sexp(tokens):
    if isinstance(tokens, str):
        return SExp(tokens.encode("utf8"))
    return [convert_list_of_lists_to_sexp(_) for _ in tokens]


def do_compile(prog):
    context = Context(defuns=[], defmacros=[], op_lookup={})
    tokens = tokenize_program(prog)
    function_rewriters = get_built_in_functions()
    local_function_rewriters = {}
    function_imps = {}
    function_name_lookup = []
    for declaration in tokens[0]:
        name, builder, imp = parse_declaration(declaration)
        local_function_rewriters[name] = builder
        function_imps[name] = imp
        function_name_lookup.append(name)
    # build the function table and put that in x0
    function_index_lookup = {v: k for k, v in enumerate(function_name_lookup)}
    function_table = []
    function_rewriters.update(local_function_rewriters)
    function_table = [
        compile_sexp(compile_sexp, function_imps[name], function_rewriters, function_index_lookup)
        for name in function_name_lookup]
    r = compile_sexp(compile_sexp, tokens[1], function_rewriters, function_index_lookup)
    r1 = SExp([REDUCE_KEYWORD, [QUOTE_KEYWORD, r], [
        CONS_KEYWORD, [QUOTE_KEYWORD, function_table], [ENV_KEYWORD]]])
    return r1


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
