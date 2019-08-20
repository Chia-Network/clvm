#!/usr/bin/env python

from setuptools import setup

from clvm.version import version

setup(
    name="clvm",
    version=version,
    packages=[
        "clvm",
    ],
    author="Chia Network, Inc.",

    author_email="kiss@chia.net",
    url="https://github.com/Chia-Network/clvm",
    license="https://opensource.org/licenses/Apache-2.0",
    description="Script compiler.",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Security :: Cryptography',
    ],)
