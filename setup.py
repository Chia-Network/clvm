#!/usr/bin/env python

from setuptools import setup

from opacity.version import version

setup(
    name="opacity",
    version=version,
    packages=[
        "clvm",
        "opacity",
        "schemas",
    ],
    author="Chia Network, Inc.",

    entry_points={
        'console_scripts':
            [
                'opc = opacity.cmds:opc',
                'opd = opacity.cmds:opd',
                'reduce = opacity.cmds:reduce',
                'reduce_core = opacity.cmds:reduce_core',
                'rewrite = opacity.cmds:rewrite',
            ]
        },
    author_email="kiss@chia.net",
    url="https://github.com/Chia-Network",
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
