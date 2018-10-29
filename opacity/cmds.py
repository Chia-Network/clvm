import argparse
import binascii
import hashlib
import sys

from .compile import compile_to_sexp, disassemble, parse_macros
from .reduce import reduce as do_reduce
from .SExp import SExp


def to_script(item):
    # let's see if it's hex
    try:
        blob = binascii.unhexlify(item)
        return SExp.from_blob(blob)
    except binascii.Error:
        pass

    try:
        return compile_to_sexp(item)
    except Exception as ex:
        pass

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
        sexp = compile_to_sexp(text, macros)
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
        "script", nargs="+", type=to_script, help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    for blob in args.script:
        text = disassemble(blob)
        print(text)


def reduce(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )
    parser.add_argument(
        "script", type=to_script, help="script in hex or uncompiled text")
    parser.add_argument(
        "solution", type=to_script, nargs="?", help="solution in hex or uncompiled text")
    args = parser.parse_args(args=args[1:])

    solution = args.solution or SExp([])
    reductions = do_reduce(args.script, solution)
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
