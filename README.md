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
