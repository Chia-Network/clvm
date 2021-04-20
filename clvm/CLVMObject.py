"""
This is the minimal `SExp` type that defines how and where its contents are
stored in the heap. The methods here are the only ones required for `run_program`.
A native implementation of `run_program` should implement this base class.
"""

# typing provides support for type hints -> https://docs.python.org/3/library/typing.html
import typing

# Set this to "1" to do a run-time type check
# This may slow things down a bit

TYPE_CHECK = 0


class CLVMObject:
    '''
    Slots "Restricts the valid set of attribute names on an object to exactly those names listed." 
    Second, since the attributes are now fixed, it is no longer necessary to store attributes in an instance dictionary, 
    so the __dict__ attribute is removed. 
    
    This improves performance of the __new__ class system. 
    
    -> Slots and __new__ according to Guidio:
    http://python-history.blogspot.com/2010/06/inside-story-on-new-style-classes.html
    '''
    # Optional[X] is a shorthand for Union[X, None]
    atom: typing.Optional[bytes]
    pair: typing.Optional[typing.Tuple["CLVMObject", "CLVMObject"]]
    __slots__ = ["atom", "pair"] 

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
