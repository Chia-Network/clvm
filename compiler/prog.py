from clvm.make_eval import EvalError

from .Node import Node
from .reader import read_tokens


def list_to_cons(sexp):
    """
    Take an sexp that is a list and turn it into a bunch of cons
    operators that build the list.
    """
    if sexp.nullp():
        return sexp.null()
    return ["cons", sexp.first(), list_to_cons(sexp.rest())]


def do_local_substitution(sexp, arg_lookup):
    if sexp.nullp():
        return sexp
    if sexp.listp():
        if not sexp.nullp() and sexp.first().as_atom() == "quote":
            return sexp
        return sexp.to([sexp.first()] + [
            do_local_substitution(_, arg_lookup) for _ in sexp.rest().as_iter()])
    b = sexp.as_atom()
    return sexp.to(arg_lookup.get(b, b))


def invoke_code_at_node(to_sexp_f, function_node, constant_node, args):
    return to_sexp_f(["eval", function_node, ["cons", constant_node, args]])


def build_arg_lookup(args, base_node=Node()):

    def iterate(args, arg_lookup, node):
        if args.nullp():
            return
        if args.listp():
            iterate(args.first(), arg_lookup, node.first())
            iterate(args.rest(), arg_lookup, node.rest())
            return
        arg_lookup[args.as_atom()] = node

    arg_lookup = {}
    iterate(args, arg_lookup, base_node)
    return arg_lookup


def parse_defun(dec, operator_lookup, function_imps):
    label, args, definition = list(dec.rest().as_iter())
    name = label.as_atom()

    # do arg substitution in definition so it's in terms of indices
    arg_lookup = build_arg_lookup(args, Node().rest())

    def builder(compile_sexp, args, function_rewriters, function_index_lookup):
        function_index = function_index_lookup[name]
        r = invoke_code_at_node(args.to, function_index, Node().first(), list_to_cons(args))
        return compile_sexp(compile_sexp, r, function_rewriters, function_index_lookup)

    operator_lookup[name] = builder
    function_imps[name] = do_local_substitution(definition, arg_lookup)


def parse_defmacro(dec, operator_lookup):
    name, args, definition = list(dec.rest().as_iter())

    arg_lookup = build_arg_lookup(args)

    def builder(compile_sexp, args, function_rewriters, function_index_lookup):
        # substitute in variables
        expanded_sexp = macro_expand(definition, arg_lookup)
        new_sexp = compile_sexp(compile_sexp, expanded_sexp, function_rewriters, function_index_lookup)
        # run it
        # BRAIN DAMAGE: TODO fix this import
        from .cmds import do_eval as eval_f
        r = eval_f(new_sexp, args)
        # compile the output and return that
        return compile_sexp(compile_sexp, r, function_rewriters, function_index_lookup)

    operator_lookup[name.as_atom()] = builder


def parse_import(dec, operator_lookup, function_imps):
    with open(dec.rest().first().as_atom(), "r") as f:
        header = f.read()
        imports = read_tokens(header)
        for sexp in imports.as_iter():
            parse_declaration(sexp, operator_lookup, function_imps)


def parse_declaration(declaration, operator_lookup, function_imps):
    if declaration.first() == "import":
        return parse_import(declaration, operator_lookup, function_imps)
    if declaration.first() == "defun":
        return parse_defun(declaration, operator_lookup, function_imps)
    if declaration.first() == "defmacro":
        return parse_defmacro(declaration, operator_lookup)
    raise EvalError("only defun, defmacro, import expected here", declaration)


def compile_atom(self, sexp, function_rewriters, function_index_lookup):
    return sexp


def compile_sexp(self, sexp, function_rewriters, function_index_lookup):
    # x0: function table
    # x1, x2...: env
    # (function_x a b c ...) => (reduce (get_raw x0 #function_x) (list x0 a b c))
    if not sexp.listp():
        return sexp
    if sexp.nullp():
        return sexp
    opcode = sexp.first().as_atom()
    if opcode == "quote":
        if sexp.rest().nullp() or not sexp.rest().rest().nullp():
            raise EvalError("quote requires 1 argument", sexp)
        return sexp.to(["quote", sexp.rest().first()])
    args = sexp.to([self(
        self, _, function_rewriters, function_index_lookup) for _ in sexp.rest().as_iter()])
    if opcode in function_rewriters:
        return function_rewriters[opcode](self, args, function_rewriters, function_index_lookup)
    return sexp.to(opcode).cons(args)


def macro_expand(definition, arg_lookup):
    if definition.listp():
        if definition.nullp():
            return definition
        t1 = [macro_expand(_, arg_lookup) for _ in definition.rest().as_iter()]
        t2 = [definition.first()]
        t3 = t2 + t1
        return definition.to(t3)

    as_atom = definition.as_atom()
    if as_atom in arg_lookup:
        return arg_lookup[as_atom]
    return definition


def op_prog_op(sexp):
    function_rewriters = {}
    local_function_rewriters = {}
    function_imps = {}
    for declaration in sexp.first().as_iter():
        parse_declaration(declaration, local_function_rewriters, function_imps)
    # build the function table and put that in x0
    base_node = Node().first()
    function_name_lookup = sorted(function_imps.keys())
    function_index_lookup = {v: base_node.list_index(k) for k, v in enumerate(function_name_lookup)}
    function_table = []
    function_rewriters.update(local_function_rewriters)
    function_table = list_to_cons(sexp.to([
        ["function", compile_sexp(
            compile_sexp, function_imps[name], function_rewriters, function_index_lookup)]
        for name in function_name_lookup]))
    r = compile_sexp(compile_sexp, sexp.rest().first(), function_rewriters, function_index_lookup)
    r1 = invoke_code_at_node(sexp.to, ["function", r], function_table, ["args"])
    return r1


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
