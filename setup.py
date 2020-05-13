#!/usr/bin/env python

import sys

from setuptools import setup

with open("README.md", "rt") as fh:
    long_description = fh.read()

try:
    from setuptools_rust import RustExtension
except ImportError:
    import subprocess

    errno = subprocess.call([sys.executable, "-m", "pip", "install", "setuptools-rust"])
    if errno:
        print("Please install setuptools-rust package")
        raise SystemExit(errno)
    else:
        from setuptools_rust import RustExtension


setup(
    name="clvm",
    packages=["clvm", "clvm.ecdsa", ],
    author="Chia Network, Inc.",
    author_email="hello@chia.net",
    url="https://github.com/Chia-Network/clvm",
    license="https://opensource.org/licenses/Apache-2.0",
    description="[Contract Language | Chialisp] Virtual Machine",
    install_requires=["setuptools_scm"],
    setup_requires=["setuptools_scm", "setuptools-rust>=0.10.1", "wheel"],
    use_scm_version={"fallback_version": "unknown"},
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Security :: Cryptography",
    ],
    rust_extensions=[RustExtension("clvm.native.clvmr")],
    project_urls={
        "Bug Reports": "https://github.com/Chia-Network/clvm",
        "Source": "https://github.com/Chia-Network/clvm",
    },
)
