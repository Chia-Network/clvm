A fork of CLVM to add documentation and explanation. 

# CLVMObject 

A [CLVM object](https://github.com/b0mTrady/clvm/blob/develop/clvm/CLVMObject.py#L2) is a:

> minimal `SExp` type that defines how and where its contents are stored in the heap

SExp stands for [S-expression](https://www.cs.unm.edu/~luger/ai-final2/LISP/CH%2011_S-expressions,%20The%20Syntax%20of%20Lisp.pdf). 

An S-expression or Symbolic Expression is commonly understood as a way to represent a nested list though the [Wizard](https://web.mit.edu/alexmv/6.037/sicp.pdf) tells us that symbolic expressions are:

> data whose elementary parts can be arbitrary symbols rather than only numbers (p. 90) 

*For further exploration see page 100 - 104 of the [Wiz](https://web.mit.edu/alexmv/6.037/sicp.pdf)*



The CLVM object makes extensive use of the [typing library](https://docs.python.org/3/library/typing.html) for type hints. 

```python

class CLVMObject:

    atom: typing.Optional[bytes]
    pair: typing.Optional[typing.Tuple["CLVMObject", "CLVMObject"]]
    __slots__ = ["atom", "pair"]

``
[Optional[X]](https://docs.python.org/3/library/typing.html#typing.Optional) is equivalent to [Union[X, None]](https://docs.python.org/3/library/typing.html#typing.Union)`



```python
    def __new__(class_, v: "SExpType"):
        if isinstance(v, CLVMObject):
            return v
        if TYPE_CHECK:
            type_ok = (
                isinstance(v, tuple)
                and len(v) == 2
                and isinstance(v[0], CLVMObject)
                and isinstance(v[1], CLVMObject)
            ) or isinstance(v, bytes)
            # uncomment next line for debugging help
            # if not type_ok: breakpoint()
            assert type_ok
        self = super(CLVMObject, class_).__new__(class_)
        if isinstance(v, tuple):
            self.pair = v
            self.atom = None
        else:
            self.atom = v
            self.pair = None
        return self

    def cons(self, right: "CLVMObject"):
        return self.__class__((self, right))


SExpType = typing.Union[bytes, typing.Tuple[CLVMObject, CLVMObject]]

```
