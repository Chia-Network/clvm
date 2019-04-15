import argparse
import binascii
import hashlib
import importlib
import sys

from .core import ReduceError
from .debug import make_tracing_f, trace_to_html
from .SExp import SExp

from sexp import reader, writer


def script(item, keyword_to_int):
    # let's see if it's hex
    try:
        blob = binascii.unhexlify(item)
        return SExp.from_blob(blob)
    except binascii.Error:
        pass

    try:
        return compile_to_sexp(item, keyword_to_int)
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

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--rewrite-actions", default="schemas.v0_0_2",
                       help="Python module imported with rewrite")
    group.add_argument("-c", "--core", action="store_true",
                       help="Don't use a derived language, just the core implementation")
    parser.add_argument("-s", "--script_hash", action="store_true", help="Show sha256 script hash")
    parser.add_argument(
        "path_or_code", nargs="*", type=path_or_code, help="path to opacity script, or literal script")
    args = parser.parse_args(args=args[1:])

    mod = schema_for_name("opacity.core" if args.core else args.rewrite_actions)

    for text in args.path_or_code:
        try:
            sexp = compile_to_sexp(text, schema.keyword_to_int)
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--rewrite-actions", default="schemas.v0_0_2",
                       help="Python module imported with rewrite")
    group.add_argument("-c", "--core", action="store_true",
                       help="Don't use a derived language, just the core implementation")
    parser.add_argument(
        "script", nargs="+", type=binascii.unhexlify, help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    schema = schema_for_name("opacity.core" if args.core else args.rewrite_actions)

    for blob in args.script:
        text = disassemble(blob, schema.keyword_from_int)
        print(text)


def trace_to_text(trace, keyword_from_int):
    for (form, env), rv in trace:
        env_str = ", ".join(dump(_) for _ in env)
        rewrit_form = form
        if form != rewrit_form:
            print("%s -> %s [%s] => %s" % (
                disassemble(form, keyword_from_int),
                disassemble(rewrit_form, keyword_from_int),
                env_str, disassemble(rv, keyword_from_int)))
        else:
            print("%s [%s] => %s" % (
                disassemble(form, keyword_from_int), env_str, disassemble(rv, keyword_from_int)))


def reduce(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--schema", default="schemas.v0_0_2",
                       help="Python module imported with rewrite")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")
    parser.add_argument(
        "solution", nargs="?", help="solution in hex or uncompiled text", default=SExp([]))

    args = parser.parse_args(args=args[1:])

    mod = importlib.import_module(args.schema)

    sexp = mod.from_tokens(reader.read_tokens(args.script))

    solution = SExp([])
    if args.solution:
        solution = mod.from_tokens(reader.read_tokens(args.solution))

    try:
        sexp = SExp([sexp] + list(solution))
        reductions = mod.transform(sexp)
        output = mod.to_tokens(reductions)
        if not args.debug:
            print(writer.write_tokens(output))
    except ReduceError as e:
        final_output = "FAIL: %s" % e
        if not args.debug:
            print(final_output)
        return -1
    finally:
        # TODO solve the debugging problem
        the_log = []
        if args.debug:
            trace_to_html(the_log, mod.keyword_from_int)
        elif args.verbose:
            trace_to_text(the_log, mod.keyword_from_int)


def rewrite(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Rewrite an opacity program in terms of the core language.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--rewrite-actions", default="schemas.v0_0_2",
                       help="Python module imported with rewrite")
    group.add_argument("-c", "--core", action="store_true",
                       help="Don't use a derived language, just the core implementation")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    schema = schema_for_name("opacity.core" if args.core else args.rewrite_actions)

    sexp = script("(rewrite %s)" % args.script, schema.keyword_to_int)

    reduce_f = schema.reduce_f

    env = SExp([])
    reductions = reduce_f(reduce_f, sexp, env)
    print(disassemble(reductions, schema.keyword_from_int))


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
