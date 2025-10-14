#!/usr/bin/env python

from setuptools import setup

with open("README.md", "rt") as fh:
    long_description = fh.read()

dependencies = [
    "chia_rs>=0.2.13",
    "importlib_metadata~=8.7",
    "typing-extensions~=4.0",
]

dev_dependencies = [
    "clvm_tools>=0.4.4",
    "mypy",
    "pytest",
    "setuptools",
    "types-setuptools",
]

setup(
    name="clvm",
    packages=[
        "clvm",
    ],
    author="Chia Network, Inc.",
    author_email="hello@chia.net",
    url="https://github.com/Chia-Network/clvm",
    license="https://opensource.org/licenses/Apache-2.0",
    description="[Contract Language | Chialisp] Virtual Machine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8.1, <4",
    install_requires=dependencies,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Security :: Cryptography",
    ],
    extras_require=dict(
        dev=dev_dependencies,
    ),
    project_urls={
        "Bug Reports": "https://github.com/Chia-Network/clvm",
        "Source": "https://github.com/Chia-Network/clvm",
    },
    package_data={
        "": ["py.typed"],
    },
)
