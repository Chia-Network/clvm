import argparse
import binascii
import hashlib
import sys

from .compile import compile_to_sexp, disassemble, dump, parse_macros
from .reduce import default_reduce_f, reduce as opacity_reduce
from .SExp import SExp


def script(item, macros={}):
    # let's see if it's hex
    try:
        blob = binascii.unhexlify(item)
        return SExp.from_blob(blob)
    except binascii.Error:
        pass

    try:
        return compile_to_sexp(item, macros=macros)
    except Exception as ex:
        print("bad script: %s" % ex.msg, file=sys.stderr)

    raise ValueError("bad value %s" % item)


def opc(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Compile an opacity script.'
    )

    def textfile(path):
        with open(path) as f:
            return f.read()

    parser.add_argument(
        "-m", "--macro", action="append", type=textfile, help="Path to preprocessing macro file")
    parser.add_argument("-c", "--code", action="append", help="Literal code to compile")
    parser.add_argument("-s", "--script_hash", action="store_true", help="Show sha256 script hash")
    parser.add_argument("path", nargs="*", type=textfile, help="path opacity script")
    args = parser.parse_args(args=args[1:])

    macros = {}
    for text in args.macro or []:
        parse_macros(text, macros)

    for text in (args.code or []) + args.path:
        try:
            sexp = compile_to_sexp(text, macros)
        except SyntaxError as ex:
            print("%s" % ex.msg)
            continue
        compiled_script = sexp.as_bin()
        script_hash = hashlib.sha256(compiled_script).hexdigest()
        if args.script_hash:
            print(script_hash)
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


def debug_frame(form, context):
    rv = default_reduce_f(form, context)
    env_str = ", ".join(dump(_) for _ in context.env)
    print("%s [%s] => %s" % (disassemble(form), env_str, disassemble(rv)))
    return rv


def reduce(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display resolve of all reductions, for debugging")
    parser.add_argument(
        "script", type=script, help="script in hex or uncompiled text")
    parser.add_argument(
        "solution", type=script, nargs="?", help="solution in hex or uncompiled text")
    args = parser.parse_args(args=args[1:])

    solution = args.solution or SExp([])
    reduce_f = None
    if args.verbose:
        reduce_f = debug_frame
    reductions = opacity_reduce(args.script, solution, reduce_f)
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
