import binascii

from clvm.make_eval import EvalError

from .expand import op_expand_op


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def parse_as_int(sexp):
    try:
        int(sexp.as_atom())
        return sexp.to(["q", sexp])
    except (ValueError, TypeError):
        pass


def parse_as_hex(sexp):
    token = sexp.as_atom()
    if token[:2].upper() == "0X":
        try:
            return sexp.to(bytes_as_hex(binascii.unhexlify(token[2:])))
        except Exception:
            raise EvalError("invalid hex", sexp)


def make_compile_remap(keyword, compiled_keyword):
    def remap(op_compile_op, sexp):
        new_args = [op_compile_op(sexp.to([_])) for _ in sexp.as_iter()]
        return sexp.to([compiled_keyword] + new_args)
    return remap


def static_eval(sexp):
    # TODO: improve, and do deep eval if possible
    operator = sexp.first()
    if not operator.listp():
        if not operator.nullp():
            as_atom = operator.as_atom()
            if as_atom == "quote":
                return sexp.rest().first()
    raise EvalError("non static value", sexp)


def compile_function_op(op_compile_op, sexp):
    new_sexp = sexp.to([static_eval(sexp.first())])
    return sexp.to(["q", op_compile_op(new_sexp)])


def make_compile_rewriters():
    REMAP_LIST = {
        "+": "+",
        "-": "-",
        "*": "*",
        "cons": "c",
        "first": "f",
        "rest": "r",
        "args": "a",
        "equal": "=",
        "eval": "e",
        "if_op": "i",
    }
    remapped = {k: make_compile_remap(k, v) for k, v in REMAP_LIST.items()}
    remapped["function_op"] = compile_function_op
    return remapped


COMPILE_REWRITERS = make_compile_rewriters()


def compile_atom(sexp):
    token = sexp.as_atom()
    c = token[0]
    if c in "\'\"":
        assert c == token[-1] and len(token) >= 2
        return sexp.to(["q", token])

    for f in [parse_as_int, parse_as_hex]:
        v = f(sexp)
        if v is not None:
            return v
    raise EvalError("can't compile token", sexp)


def op_compile_sexp(sexp):
    if not sexp.listp():
        return compile_atom(sexp)

    if sexp.nullp():
        return sexp.to(["q", sexp])

    opcode = sexp.first().as_atom()
    if opcode == "quote":
        args = sexp.rest()
        if not args.nullp() and args.rest().nullp():
            return args.to(["q", args.first()])
        raise EvalError("quote requires 1 argument", sexp)

    if opcode in COMPILE_REWRITERS:
        return COMPILE_REWRITERS[opcode](op_compile_op, sexp.rest())
    raise EvalError("can't compile opcode", sexp)


def op_compile_op(sexp):
    """
    Turn high level lisp into clvm runtime lisp.
    """
    # first, expand everything
    if not sexp.nullp() and sexp.rest().nullp():
        sexp = op_expand_op(sexp)
        return op_compile_sexp(sexp)

    raise EvalError("compile_op requires exactly 1 parameter", sexp)


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
