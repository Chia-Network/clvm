"""
This is the minimal `SExp` type that defines how and where its contents are
stored in the heap. The methods here are the only ones required for `run_program`.
A native implementation of `run_program` should implement this base class.
"""

import typing


try:
    from clvm_rs import PyNode as CLVMObject
except ImportError:
    from .PyCLVMObject import CLVMObject

SExpType = typing.Union[bytes, typing.Tuple[CLVMObject, CLVMObject]]
