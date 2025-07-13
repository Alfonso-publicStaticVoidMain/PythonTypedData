from __future__ import annotations

import collections
import types
import typing
from typing import Iterable, TypeVar, TYPE_CHECKING, Any, get_origin, get_args, Union, Annotated, Literal

if TYPE_CHECKING:
    from abstract_classes import Collection, AbstractSequence, AbstractSet, AbstractDict
    from maybe import Maybe

T = TypeVar("T")

CUSTOM_TYPE_CHECKS = {
    AbstractSequence: lambda val, args: val.item_type == args[0],
    AbstractSet: lambda val, args: val.item_type == args[0],
    AbstractDict: lambda val, args: val.key_type == args[0] and val.value_type == args[1],
    Maybe: lambda val, args: val.item_type == args[0],
}


def _validate_value(item_type: type, value: object) -> object:
    """
    Checks if a single value is of a given type, or if it can be safely converted to that type. Valid conversions for
    now are int -> float, str -> (int, float) and Any -> str provided no error is raised.
    :param value: Value to check validity of.
    :param item_type: Type to check match for the value.
    :return: The value itself if it's of item_type, or its conversion to item_type if it can be safely converted to it.
    :raise: TypeError if the value isn't of item_type and can't be safely converted to it.
    """
    if _validate_generic_class(value, item_type):
        # If the value is of the given type, it's returned unmodified.
        return value

    converted = None

    if item_type is float and isinstance(value, int):
        converted = float(value)
    elif (item_type is int or item_type is float) and isinstance(value, str):
        try:
            converted = item_type(value)
        except ValueError:
            pass
    elif item_type is str:
        try:
            converted = str(value)
        except ValueError:
            pass

    if converted is not None:
        return converted
    else:
        raise TypeError(f"Element {value!r} is not of type {item_type.__name__} and cannot be converted safely.")


def _validate_values(item_type: type, actual_values: Iterable | None) -> list:
    """
    Checks if all elements of the given Iterable are of the given type or a subclass thereof. If not, raises a TypeError.
    :param item_type: Type to check for.
    :param actual_values: Iterable of values of possibly different types.
    :return: A list of values validated as per the _validate_value function, coercing certain types like int to float
    and str to int or float if possible.
    :raise: TypeError if not all elements of the actual_values list are of type item_type.
    """
    if actual_values is None:
        return []
    validated_values = []
    for value in actual_values:
        validated_values.append(_validate_value(item_type, value))
    return validated_values


def _validate_types(
    item_type: type[T],
    other: Iterable[T] | Collection[T],
    valid_typed_types: tuple[type[Collection], ...],
    valid_built_in_types: tuple[type, ...]
) -> list:
    """
    Checks that two objects self and others hold compatible types. Self will always be assumed a typed class, while others
    will be of the parameter tuples valid_typed_typed and valid_built_in_types.
    :param item_type: Type to compare the type against.
    :param other: Typed or not object to check its contained type.
    :param valid_typed_types: Types from my typed classes that should be accepted.
    :param valid_built_in_types: Typed from Python's built ins that should be accepted.
    :return: A list containing the values contained on the others object after validating its type and converting it to
    self.item_type if necessary.
    """
    if isinstance(other, valid_typed_types):
        if not issubclass(other.item_type, item_type):
            raise ValueError(f"Different types for self ({item_type.__name__}) and others ({other.item_type.__name__})")
        other_values = other.values
    elif isinstance(other, valid_built_in_types):
        other_values = _validate_values(item_type, other)
    else:
        raise TypeError(f"{other} must be a valid type.")
    return other_values


def _validate_multiple_sets(item_type: type[T], others: Iterable[Iterable[T]]):
    from abstract_classes import Collection
    other_sets: list = []
    for iterable in others:
        other_sets.append(_validate_types(item_type, iterable, (Collection,), (Iterable,)))
    return other_sets


def _infer_type(values: Iterable[T] | Collection[T]) -> type[T]:
    if values is None or not values:
        raise ValueError("Type can't be inferred from an empty iterable or None object.")
    from abstract_classes import Collection
    if isinstance(values, Collection):
        return values.item_type

    inferred_type: type | None = None
    for value in values:
        if inferred_type is None:
            inferred_type = type(value)
        elif inferred_type != type(value):
            raise ValueError(f"There's a type mismatch: value {value} doesn't have type {inferred_type.__name__}, but {type(value).__name__}")
    return inferred_type


def _validate_type(value: Any, expected_type: Any) -> bool:
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is None:
        return isinstance(value, expected_type)

    if origin in (Union, types.UnionType):
        return any(_validate_type(value, arg) for arg in args)

    if origin is Annotated:
        # Ignore metadata for validation purposes
        return _validate_type(value, args[0])

    if origin is Literal:
        return value in args

    if origin is tuple:
        return _validate_tuple(value, args)

    if origin in (list,):
        return _validate_list(value, args)

    if origin in (set, frozenset):
        return _validate_set(value, origin, args)

    if origin in (dict,):
        return _validate_dict(value, args)

    if origin in (typing.Mapping, collections.abc.Mapping):
        return _validate_mapping(value, args)

    if origin in (typing.Sequence, collections.abc.Sequence):
        return _validate_sequence(value, args)

    # Fallback to structural check
    return isinstance(value, origin)


def _validate_tuple(value: Any, args: tuple) -> bool:
    if not isinstance(value, tuple):
        return False

    # Handle Tuple[T, ...] (homogeneous)
    if len(args) == 2 and args[1] is Ellipsis:
        return all(_validate_type(v, args[0]) for v in value)

    # Heterogeneous tuple: Tuple[T1, T2, T3]
    if len(value) != len(args):
        return False
    return all(_validate_type(v, t) for v, t in zip(value, args))


def _validate_list(value: Any, args: tuple) -> bool:
    if not isinstance(value, list):
        return False
    (item_type,) = args
    return all(_validate_type(v, item_type) for v in value)


def _validate_set(value: Any, set_type: type, args: tuple) -> bool:
    if not isinstance(value, set_type):
        return False
    (item_type,) = args
    return all(_validate_type(v, item_type) for v in value)


def _validate_dict(value: Any, args: tuple) -> bool:
    if not isinstance(value, dict):
        return False
    key_type, val_type = args
    return all(_validate_type(k, key_type) and _validate_type(v, val_type) for k, v in value.items())


def _validate_mapping(value: Any, args: tuple) -> bool:
    if not isinstance(value, collections.abc.Mapping):
        return False
    key_type, val_type = args
    return all(_validate_type(k, key_type) and _validate_type(v, val_type) for k, v in value.items())


def _validate_sequence(value: Any, args: tuple) -> bool:
    if not isinstance(value, collections.abc.Sequence) or isinstance(value, str):
        return False
    (item_type,) = args
    return all(_validate_type(v, item_type) for v in value)


def _validate_generic_class(value: Any, expected_type: Any) -> bool:
    origin = type(expected_type)
    if not isinstance(value, expected_type):
        return False

    args = get_args(expected_type)

    for base, checker in CUSTOM_TYPE_CHECKS.items():
        if isinstance(value, base):
            return checker(value, args)

    return True

