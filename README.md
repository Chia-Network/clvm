This is the in-development version of a LISP-like language for encumbering and releasing funds with smart-contract capabilities.

See docs/clvm.org for more info.


Testing
=======

    $ pip install -r requirements-dev.txt
    $ py.test tests


Example
=======

Here's an example on how to create a script and invoke it from python.

    $ python
    >>> from clvm import to_sexp_f, run_program, KEYWORD_TO_ATOM
    >>> program = to_sexp_f([KEYWORD_TO_ATOM["q"], 100])     # (q 100)
    >>> args = to_sexp_f([])
    >>> r = run_program(program, args)
    >>> print(r.listp())
    False
    >>> print(r.as_int())
    100
    >>>
    >>> program = to_sexp_f([KEYWORD_TO_ATOM["+"], [KEYWORD_TO_ATOM["q"], 500], \
    ...                     [KEYWORD_TO_ATOM["f"], [KEYWORD_TO_ATOM["a"]]]])     # (+ (q 500) (f (a)))
    >>> args = to_sexp_f([25])   # (25)
    >>> r = run_program(program, args)
    >>> print(r.listp())
    False
    >>> print(r.as_int())
    525
    >>>
    >>> program = to_sexp_f([KEYWORD_TO_ATOM["c"], \
    ...                     [KEYWORD_TO_ATOM["f"], [KEYWORD_TO_ATOM["r"], [KEYWORD_TO_ATOM["a"]]]], \
    ...                     [KEYWORD_TO_ATOM["f"], [KEYWORD_TO_ATOM["a"]]]])     # (c (f (r (a))) (f (a)))
    >>> args = to_sexp_f([45, 55])
    >>> r = run_program(program, args)
    >>> print(r.listp())
    True
    >>> print(r.first().as_int())
    55
    >>> print(r.rest().as_int())
    45
