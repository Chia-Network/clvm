import binascii

from clvm.make_eval import EvalError

from .Node import Node


def list_to_cons(sexp):
    """
    Take an sexp that is a list and turn it into a bunch of cons
    operators that build the list.
    """
    if sexp.nullp():
        return sexp.null()
    return ["cons", sexp.first(), list_to_cons(sexp.rest())]


def do_local_subsitution(sexp, arg_lookup):
    if sexp.listp():
        if not sexp.nullp() and sexp.first().as_atom() == "quote":
            return sexp
        return sexp.to([sexp.first()] + [
            do_local_subsitution(_, arg_lookup) for _ in sexp.rest().as_iter()])
    b = sexp.as_atom()
    return sexp.to(arg_lookup.get(b))


def invoke_code_at_node(to_sexp_f, function_node, constant_node, args):
    return to_sexp_f(["eval", function_node, ["cons", constant_node, args]])


def parse_defun(dec):
    name, args, definition = list(dec.rest().as_iter())

    # do arg substitution in definition so it's in terms of indices
    base_node = Node().rest()
    arg_lookup = {_.as_atom(): base_node.list_index(index) for index, _ in enumerate(args.as_iter())}

    def builder(compile_sexp, args, function_rewriters, function_index_lookup):
        function_index = function_index_lookup[name.as_atom()]
        r = invoke_code_at_node(args.to, function_index, Node(), list_to_cons(args))
        return compile_sexp(compile_sexp, r, function_rewriters, function_index_lookup)

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
    raise EvalError("only defun and defmacro expected here", declaration)


def compile_atom(self, sexp, function_rewriters, function_index_lookup):
    return sexp


def compile_sexp(self, sexp, function_rewriters, function_index_lookup):
    # x0: function table
    # x1, x2...: env
    # (function_x a b c ...) => (reduce (get_raw x0 #function_x) (list x0 a b c))
    if not sexp.listp():
        return sexp
    opcode = sexp.first().as_atom()
    if opcode == "quote":
        if sexp.rest().nullp() or not sexp.rest().rest().nullp():
            raise EvalError("quote requires 1 argument", sexp)
        return sexp.to(["q", sexp.rest().first()])
    if opcode in function_rewriters:
        return function_rewriters[opcode](self, sexp.rest(), function_rewriters, function_index_lookup)
    return sexp


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
    function_name_lookup = []
    for declaration in sexp.first().as_iter():
        name, builder, imp = parse_declaration(declaration)
        local_function_rewriters[name] = builder
        if imp is not None:
            function_imps[name] = imp
            function_name_lookup.append(name)
    # build the function table and put that in x0
    base_node = Node().first()
    function_index_lookup = {v: base_node.list_index(k) for k, v in enumerate(function_name_lookup)}
    function_table = []
    function_rewriters.update(local_function_rewriters)
    function_table = [
        compile_sexp(compile_sexp, function_imps[name], function_rewriters, function_index_lookup)
        for name in function_name_lookup]
    r = compile_sexp(compile_sexp, sexp.rest().first(), function_rewriters, function_index_lookup)
    r1 = invoke_code_at_node(sexp.to, ["quote", r], ["quote", function_table], ["args"])
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
