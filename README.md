[![Coverage Status](https://coveralls.io/repos/github/Chia-Network/clvm/badge.svg?branch=main)](https://coveralls.io/github/Chia-Network/clvm?branch=main)

This is the in-development version of a LISP-like language for encumbering and releasing funds with smart-contract capabilities.

See docs/clvm.org or https://chialisp.com/ for more info.


Testing
=======

    $ python3 -m venv venv
    $ . ./venv/bin/activate
    $ pip install -e '.[dev]'
    $ pytest tests

