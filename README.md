This is the in-development version of Chiascript "opacity", a LISP-like language for encumbering and releasing funds with smart-contract capabilities.

See docs/CHIASCRIPT-BY-EXAMPLE.md.html for more info.


Set up your virtual environments:

    $ python3 -m venv env
    $ ln -s env/bin/activate
    $ . ./activate
    $ pip install -e .

Check out the command-line tools help info:

    $ opc -h
    $ opd -h
    $ reduce -h

Try the command-line tools to create and reduce scripts.

    $ opc '(equal 10 10)'
    23080a0a
    $ opd 23080a0a
    (equal 10 10)
    $ opc '(equal x0 (+ x1 x2))'
    230840230b4142
    $ opd 230840230b4142
    (equal x0 (+ x1 x2))
    $ opc '(18 10 8)'
    23120a08
    $ reduce 230840230b4142 23120a08
    1
    $ reduce `opc '(equal x0 (+ x1 x2))'` `opc '(18 10 8)'`
    1
    $ reduce `opc '(equal x0 (+ x1 x2))'` `opc '(18 10 7)'`
    0


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
