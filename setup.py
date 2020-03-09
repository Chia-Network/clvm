#!/usr/bin/env python

from setuptools import setup

setup(
    name="clvm",
    packages=["clvm", "clvm.ecdsa",],
    author="Chia Network, Inc.",
    author_email="hello@chia.net",
    url="https://github.com/Chia-Network/clvm",
    license="https://opensource.org/licenses/Apache-2.0",
    description="[Contract Language | Chialisp] Virtual Machine",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Security :: Cryptography",
    ],
    project_urls={
        "Bug Reports": "https://github.com/Chia-Network/clvm",
        "Source": "https://github.com/Chia-Network/clvm",
    },
)
