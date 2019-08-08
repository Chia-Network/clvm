This is the in-development version of Chiascript "opacity", a LISP-like language for encumbering and releasing funds with smart-contract capabilities.

See docs/CHIASCRIPT-BY-EXAMPLE.md.html for more info.


Set up your virtual environments:

    $ python3 -m venv env
    $ ln -s env/bin/activate
    $ . ./activate
    $ pip install -e .

The language has two components: the higher level language and the compiled lower level language which runs on the clvm.
To compile the higher level language into the lower level language use:

    $ run '(compile (+ 2 3))'
    (+ (q 2) (q 3))

To execute this code:

    $ brun '(+ (q 2) (q 3))'
    5

Schemas are used to specify the macros which will be compiled into the core language. Users will eventually be able to specify their own custom schemas which will act as header files and allow them to use less common macros.

You can read more about the core language [here](./docs/clvm.org)

Here are some more examples of arguments being passed in during evaluation.

    $ run '(compile (+ x0 3))'
    (+ (f (a)) (q 3))
    $ brun '(+ (f (a)) (q 3))' '(90)'
    93

    $ brun '(+ (e (f (a)) (q ())) (q 3))' '((+ (q 3) (q 3)))'
    9



From python
===========

Here's an example on how to create a script and invoke it from python.

    $ python
    >>> from clvm import to_sexp_f, eval_f, KEYWORD_TO_ATOM
    >>> program = to_sexp_f([KEYWORD_TO_ATOM["q"], 100])     # (q 100)
    >>> args = to_sexp_f([])
    >>> r = eval_f(eval_f, program, args)
    >>> print(r.listp())
    False
    >>> print(r.as_int())
    100
    >>>
    >>> program = to_sexp_f([KEYWORD_TO_ATOM["+"], [KEYWORD_TO_ATOM["q"], 500], \
    ...                     [KEYWORD_TO_ATOM["f"], [KEYWORD_TO_ATOM["a"]]]])     # (+ (q 500) (f (a)))
    >>> args = to_sexp_f([25])   # (25)
    >>> r = eval_f(eval_f, program, args)
    >>> print(r.listp())
    False
    >>> print(r.as_int())
    525
    >>>
    >>> program = to_sexp_f([KEYWORD_TO_ATOM["c"], \
    ...                     [KEYWORD_TO_ATOM["f"], [KEYWORD_TO_ATOM["r"], [KEYWORD_TO_ATOM["a"]]]], \
    ...                     [KEYWORD_TO_ATOM["f"], [KEYWORD_TO_ATOM["a"]]]])     # (c (f (r (a))) (f (a)))
    >>> args = to_sexp_f([45, 55])
    >>> r = eval_f(eval_f, program, args)
    >>> print(r.listp())
    True
    >>> print(r.first().as_int())
    55
    >>> print(r.rest().as_int())
    45
