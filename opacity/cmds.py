import argparse
import binascii
import hashlib
import sys

from .compile import compile_text, parse_macros


def create_opc_parser():
    parser = argparse.ArgumentParser(
        description='Compile an opacity script.'
    )
    parser.add_argument("-m", "--macro", help="Path to preprocessing macro file", action="append")
    parser.add_argument("path", help="path opacity script", nargs="+")
    return parser


def opc(args=sys.argv):
    parser = create_opc_parser()
    args = parser.parse_args(args=args[1:])

    macros = {}
    for path in args.macro or []:
        with open(path, "r") as f:
            text = f.read()
            parse_macros(text, macros)

    for path in args.path:
        with open(path, "r") as f:
            text = f.read()
            compiled_script = compile_text(text, macros)
            script_hash = hashlib.sha256(compiled_script).hexdigest()
            print(script_hash)
            print(binascii.hexlify(compiled_script).decode())


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
