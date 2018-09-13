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

    $ opc -c '(equal 10 10)'
    9308a10aa10a
    $ opd 9308a10aa10a
    (equal 10 10)
    $ opc -c '(equal x0 (+ x1 x2))'
    9308ff930bfefd
    $ opd 9308ff930bfefd
    (equal x0 (+ x1 x2))
    $ opc -c '(18 10 8)'
    93a112a10aa108
    $ reduce 9308ff930bfefd 93a112a10aa108
    1
    $ reduce `opc -c '(equal x0 (+ x1 x2))'` `opc -c '(18 10 8)'`
    1
    $ reduce `opc -c '(equal x0 (+ x1 x2))'` `opc -c '(18 10 7)'`
    0
