from __future__ import annotations

from types import UnionType
from typing import TypeVarTuple, Any, get_args, get_origin, Union, ClassVar, Callable
from weakref import WeakValueDictionary

"""
Inheritance tree:

GenericBase[*Ts]
│
├── Collection[T]
│    │
│    ├── MutableCollection[T] 
│    │    └──────────────────────────────────┐
│    │                                       │
│    ├── AbstractSequence[T]                 │
│    │    ├── ImmutableList[T] (*)           │
│    │    └── AbstractMutableSequence[T] ────┤
│    │         └── MutableList[T] (*)        │
│    │                                       │
│    └── AbstractSet[T]                      │
│         ├── ImmutableSet[T] (*)            │
│         └── AbstractMutableSet[T] ─────────┘
│              └── MutableSet[T] (*)
│
├── AbstractDict[K, V]
│    ├── ImmutableDict[K, V] (*)
│    └── AbstractMutableDict[K, V]
│         └── MutableDict[K, V] (*)
│
└── Maybe[T] (*)


(*) := Concrete class implementations. Everything else should be impossible to directly instantiate.
"""

Ts = TypeVarTuple("Ts")


def base_class[T: GenericBase](obj: T) -> type[T]:
    return type(obj)._origin if hasattr(type(obj), '_origin') else type(obj)

def forbid_instantiation(cls):
    """
    Class decorator that forbids direct instantiation of the decorated class with or without generics.

    :raises TypeError: If the decorated class is instantiated directly, but allows instantiation of its subclasses.
    """

    def __new__(subcls, *args, **kwargs):
        if getattr(subcls, "_origin", None) is cls:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated, even with generics.")
        if subcls is cls:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated directly.")
        return object.__new__(subcls)

    cls.__new__ = staticmethod(__new__)
    return cls


def class_name(cls: type) -> str:
    """
    Gives a str representation of a given type or class, including generics info handled recursively.

    :param cls: Class whose name will be represented.
    :return: If the type is a Union or UnionType, it's represented using the pipe operator |. If it's a class that
    extends GenericBase (it has an _args attribute), then it is assumed the class has already been properly formatted
    within the __class_getitem__ method it inherited from GenericBase.

    Then the methods get_origin and get_args from typing are used to fetch info about the base class and its generics
    to reconstruct a representation that displays that information. If that wasn't possible, a fallback is present using
    __name__ and repr.
    """

    # Case 0: Handle Union[...] using | notation
    origin = get_origin(cls)
    args = get_args(cls)
    if origin in (Union, UnionType):
        return " | ".join(class_name(arg) for arg in args)

    # Case 1: A class extending GenericBase
    if hasattr(cls, "_args"):
        return cls.__name__  # It's already been formatted

    # Case 2: Built-in generics list[int], dict[str, int], etc.
    if origin:
        origin_name = getattr(origin, '__name__', repr(origin))
        args_str = ", ".join(class_name(arg) for arg in args)
        return f"{origin_name}[{args_str}]"

    # Case 3: Simple class
    if hasattr(cls, '__name__'):
        return cls.__name__

    # Fallback for things like typing.Any
    return repr(cls)


def _convert_to(tp: type) -> Callable[[Any], Any]:
    """
    Generates a function that converts its one parameter to the type tp, only if it wasn't already of that type.

    :param tp: Type to convert into. Must also be a 1-parameter callable.
    :type tp: type

    :return: A 1-parameter callable that, for its parameter x, if it is of type tp, returns it unmodified. Otherwise,
     returns tp applied to x.
    :rtype: Callable[[Any], Any
    """
    return lambda x : x if isinstance(x, tp) else tp(x)


@forbid_instantiation
class GenericBase[*Ts]:
    """
    Top-most class in the inheritance tree, that encodes the behaviour of the classes storing their generic parameters
    received at their instantiation and storing them as a tuple in an _args attribute, as well as an _origin attribute
    pointing to the class the generics were applied upon.

    The attribute _generic_type_registry keeps a registry of all the instances of a class with certain generics that
    have already been created, so when a new one is called, it tries to retrieve it from the registry before committing
    the memory to creating a new subclass.

    Attributes:
        _generic_type_registry (ClassVar[WeakValueDictionary[tuple[type, tuple[type, ...]], type]]): A class attribute
         dict that stores the previous calls of the __class_getitem__ method to reduce memory overload and avoid
         recreating new subclasses that have already been created, retrieving them from this dict instead.

        _args (ClassVar[tuple[type, ...]]): A class attribute storing a tuple of types the class was called upon.

        _origin (ClassVar[type]): A class attribute storing the base class that was called upon one or more generic types.
    """

    _generic_type_registry: ClassVar[WeakValueDictionary[tuple[type, tuple[type, ...]], type]] = WeakValueDictionary()
    _args: ClassVar[tuple[type, ...]]
    _origin: ClassVar[type]

    @classmethod
    def __class_getitem__(cls, item: type | UnionType | tuple[type, ...]):
        """
        Extends the class cls to store the generic arguments it was called upon (item) and use them on runtime.

        :param item: type or tuple of types that represents the generic types applied to the class.
        :type item: type | tuple[type, ...]

        :return: A class inheriting from cls with the generic arguments stored on an _args attribute and the original
        class on an _origin attribute.
        :rtype: type[cls]
        """
        if not isinstance(item, tuple):
            item = (item,)

        cache_key = (cls, item)
        if cache_key in GenericBase._generic_type_registry:
            return GenericBase._generic_type_registry[cache_key]

        subclass = type(
            f"{cls.__name__}[{", ".join(class_name(arg) for arg in item)}]",
            (cls,),
            {}
        )

        subclass._args = item
        subclass._origin = cls
        GenericBase._generic_type_registry[cache_key] = subclass
        return subclass
