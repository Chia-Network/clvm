from typing import Any, Callable, Dict, Tuple, Union


CLVMAtom = Any
CLVMPair = Any

CLVMObjectType = Union["CLVMAtom", "CLVMPair"]

MultiOpFn = Callable[[bytes, CLVMObjectType, int], Tuple[int, CLVMObjectType]]

ConversionFn = Callable[[CLVMObjectType], CLVMObjectType]

OpFn = Callable[[CLVMObjectType, int], Tuple[int, CLVMObjectType]]

OperatorDict = Dict[bytes, Callable[[CLVMObjectType, int], Tuple[int, CLVMObjectType]]]
