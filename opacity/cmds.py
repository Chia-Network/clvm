import argparse
import binascii
import hashlib
import importlib
import io
import sys

from . import reader, writer

from .core import ReduceError
from .debug import trace_to_html, trace_to_text
from .SExp import SExp


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
    parser.add_argument("-s", "--schema", default="schemas.v0_0_2",
                        help="Python module imported with rewrite")
    parser.add_argument("-H", "--script_hash", action="store_true", help="Show sha256 script hash")
    parser.add_argument(
        "path_or_code", nargs="*", type=path_or_code, help="path to opacity script, or literal script")

    args = parser.parse_args(args=args[1:])

    mod = importlib.import_module(args.schema)

    for text in args.path_or_code:
        try:
            sexp = mod.from_tokens(reader.read_tokens(text))
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
    parser.add_argument("-s", "--schema", default="schemas.v0_0_2",
                        help="Python module imported with rewrite")
    parser.add_argument(
        "script", nargs="+", type=binascii.unhexlify, help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    mod = importlib.import_module(args.schema)

    for blob in args.script:
        sexp = SExp.from_stream(io.BytesIO(blob))
        output = mod.to_tokens(sexp)
        print(writer.write_tokens(output))


def reduce(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Dump debug information to html")
    parser.add_argument("-s", "--schema", default="schemas.v0_0_2",
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
    do_reduction(args, mod, sexp, solution)


def do_reduction(args, mod, sexp, solution):
    try:
        reductions = mod.transform(SExp([sexp] + list(solution)))
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
    parser.add_argument("-s", "--schema", default="schemas.v0_0_2",
                        help="Python module imported with rewrite")
    parser.add_argument(
        "script", help="script in hex or uncompiled text")

    args = parser.parse_args(args=args[1:])

    mod = importlib.import_module(args.schema)

    solution = SExp([])
    sexp = mod.from_tokens(reader.read_tokens("(rewrite %s)" % args.script))
    do_reduction(args, mod, sexp, solution)


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
