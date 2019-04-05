import argparse
import binascii
import hashlib
import importlib
import sys

from .compile import compile_to_sexp, disassemble, dump
from .core import make_reduce_f, ReduceError
from .core_operators import minimal_ops
from .debug import trace_to_html
from .keywords import KEYWORD_TO_INT
from .SExp import SExp


def script(item):
    # let's see if it's hex
    try:
        blob = binascii.unhexlify(item)
        return SExp.from_blob(blob)
    except binascii.Error:
        pass

    try:
        return compile_to_sexp(item)
    except Exception as ex:
        print("bad script: %s" % ex.msg, file=sys.stderr)

    raise ValueError("bad value %s" % item)


def load_code(args):
    for text in (args.code or []) + args.path:
        try:
            sexp = compile_to_sexp(text)
        except SyntaxError as ex:
            print("%s" % ex.msg)
            continue
        compiled_script = sexp.as_bin()
        if args.script_hash:
            print(hashlib.sha256(compiled_script).hexdigest())
        print(binascii.hexlify(compiled_script).decode())


def path_or_code(arg):
    try:
        with open(arg) as f:
            return f.read()
    except IOError:
        return arg


def opc(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Compile an opacity script.'
    )

    parser.add_argument("-s", "--script_hash", action="store_true", help="Show sha256 script hash")
    parser.add_argument(
        "path_or_code", nargs="*", type=path_or_code, help="path to opacity script, or literal script")
    args = parser.parse_args(args=args[1:])

    for text in args.path_or_code:
        try:
            sexp = compile_to_sexp(text)
        except SyntaxError as ex:
            print("%s" % ex.msg)
            continue
        compiled_script = sexp.as_bin()
        if args.script_hash:
            print(hashlib.sha256(compiled_script).hexdigest())
        print(binascii.hexlify(compiled_script).decode())


def opd(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Disassemble a compiled opacity script.'
    )
    parser.add_argument(
        "script", nargs="+", type=binascii.unhexlify, help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    for blob in args.script:
        text = disassemble(blob)
        print(text)


def trace_to_text(trace):
    for form, rewrit_form, env, rv in trace:
        env_str = ", ".join(dump(_) for _ in env)
        if form != rewrit_form:
            print("%s -> %s [%s] => %s" % (
                disassemble(form), disassemble(rewrit_form), env_str, disassemble(rv)))
        else:
            print("%s [%s] => %s" % (disassemble(form), env_str, disassemble(rv)))


def reduce(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    parser.add_argument("-r", "--rewrite-actions", default="schemas.v0_0_1",
                        help="Python module imported with rewrite")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")
    parser.add_argument(
        "solution", type=script, nargs="?", help="solution in hex or uncompiled text", default=SExp([]))

    do_reduce_tool(parser, args)


def reduce_core(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce a core opacity script.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    parser.add_argument("-r", "--rewrite-actions",
                        help="Python module imported with rewrite")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")
    parser.add_argument(
        "solution", type=script, nargs="?", help="solution in hex or uncompiled text", default=SExp([]))

    do_reduce_tool(parser, args)


def default_rewrite(self, form):
    return form


def make_rewriting_reduce(rewrite_f, reduce_f, log_reduce_f):
    def my_reduce_f(self, form, env):
        rewritten_form = rewrite_f(rewrite_f, form)
        rv = reduce_f(self, rewritten_form, env)
        log_reduce_f(SExp([form, rewritten_form, env, rv]))
        return rv
    return my_reduce_f


def do_reduce_tool(parser, args):
    args = parser.parse_args(args=args[1:])

    operator_lookup = minimal_ops(KEYWORD_TO_INT)

    core_reduce_f = make_reduce_f(operator_lookup, KEYWORD_TO_INT)

    rewrite_f = default_rewrite
    if args.rewrite_actions:
        mod = importlib.import_module(args.rewrite_actions)
        rewrite_f = mod.make_rewrite_f(KEYWORD_TO_INT, core_reduce_f, reduce_constants=False)
        d = {}
        for keyword, op_f in mod.DOMAIN_OPERATORS:
            d[KEYWORD_TO_INT[keyword]] = op_f
        operator_lookup.update(d)

        def op_rewrite(items):
            return rewrite_f(rewrite_f, items[0])

        operator_lookup[KEYWORD_TO_INT["rewrite_op"]] = op_rewrite

    sexp = script(args.script)

    the_log = []
    rewriting_reduce_f = make_rewriting_reduce(rewrite_f, core_reduce_f, the_log.append)

    try:
        reductions = rewriting_reduce_f(rewriting_reduce_f, sexp, args.solution)
        final_output = disassemble(reductions)
        if not args.debug:
            print(final_output)
    except ReduceError as e:
        final_output = "FAIL: %s" % e
        if not args.debug:
            print(final_output)
        return -1
    finally:
        if args.debug:
            trace_to_html(the_log)
        elif args.verbose:
            trace_to_text(the_log)


def rewrite(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Rewrite an opacity program in terms of the core language.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    parser.add_argument("-r", "--rewrite-actions", default="schemas.v0_0_1",
                        help="Python module imported with rewrite")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    operator_lookup = minimal_ops(KEYWORD_TO_INT)

    reduce_f = make_reduce_f(operator_lookup, KEYWORD_TO_INT)

    if args.rewrite_actions:
        mod = importlib.import_module(args.rewrite_actions)
        rewrite_f = mod.make_rewrite_f(KEYWORD_TO_INT, reduce_f, reduce_constants=False)
        d = {}
        for keyword, op_f in mod.DOMAIN_OPERATORS:
            d[KEYWORD_TO_INT[keyword]] = op_f
        operator_lookup.update(d)

    sexp = script(args.script)

    reductions = rewrite_f(rewrite_f, sexp)
    print(disassemble(reductions))


"""
Copyright 2018 Chia Network Inc

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
