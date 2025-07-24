from types import UnionType
from typing import TypeVarTuple, Any, get_args, get_origin, Union, ClassVar, TypeVar
from weakref import WeakValueDictionary

Ts = TypeVarTuple("Ts")

class GenericBase[*Ts]:
    """
    Top-most class in the inheritance tree, that encodes the behaviour of the classes storing their generic parameters
    received at their instantiation and storing them as a tuple in an _args attribute, as well as an _origin attribute
    pointing to the class the generics were applied upon.

    The attribute _generic_type_registry keeps a registry of all the instances of a class with certain generics that
    have already been created, so when a new one is called, it tries to retrieve it from the registry before committing
    the memory to creating a new subclass.
    """

    _generic_type_registry: ClassVar[WeakValueDictionary[tuple[type, tuple[type, ...]], type]] = WeakValueDictionary()
    _args: ClassVar[tuple[type, ...]]
    _origin: ClassVar[type]

    @classmethod
    def __class_getitem__(cls, item: type | tuple[type, ...]):
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
        if cache_key in cls._generic_type_registry:
            return cls._generic_type_registry[cache_key]

        subclass = type(
            f"{cls.__name__}[{", ".join(class_name(arg) for arg in item)}]",
            (cls,),
            {}
        )

        subclass._args = item
        subclass._origin = cls
        GenericBase._generic_type_registry[cache_key] = subclass
        return subclass


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
    if origin is Union or origin is UnionType:
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