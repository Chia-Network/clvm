import argparse
import binascii
import hashlib
import sys

from .compile import compile_text, disassemble, parse_macros
from .reduce import reduce as do_reduce
from .serialize import unwrap_blob, wrap_blobs


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
        compiled_script = compile_text(text, macros)
        script_hash = hashlib.sha256(compiled_script).hexdigest()
        if args.script_hash:
            print(script_hash)
        print(binascii.hexlify(compiled_script).decode())


def opd(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Disassemble a compiled opacity script.'
    )
    parser.add_argument(
        "hexstring", nargs="+", type=binascii.unhexlify, help="hex version of opacity script")
    args = parser.parse_args(args=args[1:])

    for blob in args.hexstring:
        text = disassemble(blob)
        print(text)


def reduce(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Reduce an opacity script.'
    )
    parser.add_argument(
        "script_hex", type=binascii.unhexlify, help="hex version of script")
    parser.add_argument(
        "solution_hex", type=binascii.unhexlify, help="hex version of solution")
    args = parser.parse_args(args=args[1:])

    reductions = do_reduce(unwrap_blob(args.script_hex), unwrap_blob(args.solution_hex))
    print(disassemble(wrap_blobs(reductions)))


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
