from __future__ import annotations

import collections
import types
import typing
from typing import Iterable, TypeVar, Any, get_origin, get_args, Union, Annotated, Literal

from abstract_classes import Collection, AbstractSequence, AbstractSet, AbstractDict
from concrete_classes import MutableList, ImmutableList, MutableSet, ImmutableSet, MutableDict, ImmutableDict
from maybe import Maybe

T = TypeVar("T")

COLLECTION_CLASSES = (MutableList, ImmutableList, MutableSet, ImmutableSet)
DICTIONARY_CLASSES = (MutableDict, ImmutableDict)


def _validate_value(
    expected_type: Any,
    value: Any
) -> None:
    """
    Raises TypeError if value is not of expected_type.
    """
    if not _validate_type(value, expected_type):
        raise TypeError(f"Value {value!r} is not of expected type {expected_type}")


def _validate_or_coerce_value(
    expected_type: type[T],
    value: object,
    coerce: bool = True
) -> T:
    """
    Coerces a value to a given type, returning it unmodified if it already is of that type. Valid conversions for
    now are int -> float, str -> (int, float) and Any -> str, provided no error is raised.
    :param value: Value to check validity of.
    :param expected_type: Type to check match for the value.
    :return: The value itself if it's of item_type, or its conversion to item_type if it can be safely converted to it.
    :raise: TypeError if the value isn't of item_type and can't be safely converted to it.
    """
    if _validate_type(value, expected_type):
        # If the value is of the given type, it's returned unmodified.
        return value

    if not coerce:
        raise TypeError(f"Value {value!r} is not of expected type {expected_type.__name__}")

    converted = None

    if expected_type is float and isinstance(value, int):
        converted = float(value)
    elif (expected_type is int or expected_type is float) and isinstance(value, str):
        try:
            converted = expected_type(value)
        except ValueError:
            pass
    elif expected_type is str:
        try:
            converted = str(value)
        except ValueError:
            pass

    if converted is not None:
        return converted

    raise TypeError(f"Element {value!r} is not of type {expected_type.__name__} and cannot be converted safely to it.")


def _validate_iterable(
    expected_type: type[T],
    values: Iterable[Any] | None,
) -> None:
    for value in values:
        _validate_value(expected_type, value)


def _validate_or_coerce_iterable(
    item_type: type[T],
    actual_values: Iterable[Any] | None,
    coerce: bool = True
) -> list[T]:
    """
    Coerces all elements of an Iterable.
    :param item_type: Type to coerce the elements to.
    :param values: Iterable object to coerce its elements into.
    :return: A list containing all elements after performing coercion.
    :raise: An Error will be raised if any coercion isn't possible.
    """
    if actual_values is None:
        return []
    return [_validate_or_coerce_value(item_type, value, coerce) for value in actual_values]


def _validate_collection_type_and_get_values(
    item_type: type[T],
    other: Iterable[T] | Collection[T],
    valid_typed_types: tuple[type[Collection], ...] = (Collection,),
    valid_built_in_types: tuple[type, ...] = (Iterable,),
    coerce: bool = True
) -> list[T]:
    """
    Checks that an Iterable or Collection object other holds values of type item_type and that is of a given allowed
    type from among this library's typed types or Python's built-ins. Returns a list containing the values it held,
    after performing type coercion.
    :param item_type: Type to compare the type against.
    :param other: Typed or not object to check its contained type.
    :param valid_typed_types: Types from my typed classes that should be accepted.
    :param valid_built_in_types: Typed from Python's built ins that should be accepted.
    :return: A list containing the values contained on the others object after validating its type and converting it to
    self.item_type if necessary.
    """
    if isinstance(other, valid_typed_types):
        if not issubclass(other.item_type, item_type):
            raise ValueError(f"Type mismatch between expected type {item_type.__name__} and actual: {other.item_type.__name__}")
        other_values = _validate_or_coerce_iterable(item_type, other.values, coerce)
    elif isinstance(other, valid_built_in_types):
        other_values = _validate_or_coerce_iterable(item_type, other, coerce)

    else:
        raise TypeError(f"{other} must be a valid type.")

    return other_values


def _validate_iterable_of_iterables_and_get(
    item_type: type[T],
    others: Iterable[Iterable[T]],
    coerce: bool = True
) -> list[list[T]]:
    from abstract_classes import Collection
    other_iterables: list = []
    for iterable in others:
        other_iterables.append(_validate_collection_type_and_get_values(item_type, iterable, (Collection,), (Iterable,), coerce))
    return other_iterables


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


def _validate_type_of_iterable(values: Iterable[Any], expected_type: type) -> bool:
    return all([_validate_type(value, expected_type) for value in values])


def _validate_type(value: Any, expected_type: type) -> bool:
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin in (Union, types.UnionType):
        return any(_validate_type(value, arg) for arg in args)

    if origin is Annotated:
        return _validate_type(value, args[0])

    if origin is Literal:
        return value in args

    if origin is tuple:
        return _validate_tuple(value, args)

    if origin in (list, set, frozenset, collections.abc.Sequence) or origin in COLLECTION_CLASSES:
        return _validate_iterable(value, origin, args[0])

    if origin in (collections.abc.Mapping, dict) or origin in DICTIONARY_CLASSES:
        return _validate_mapping_type(value, origin, args)

    if origin is Maybe:
        return _validate_maybe(value, origin, args)

    if origin is None:
        return isinstance(value, expected_type)

    return False


def _validate_mapping_type(value: Any, mapping_type: type, args: tuple) -> bool:
    if not isinstance(value, mapping_type):
        return False
    key_type, val_type = args
    return all(_validate_type(k, key_type) and _validate_type(v, val_type) for k, v in value.items())


def _validate_tuple(value: Any, args: tuple) -> bool:
    if not isinstance(value, tuple):
        return False
    if len(args) == 2 and args[1] is Ellipsis:
        return all(_validate_type(v, args[0]) for v in value)
    if len(value) != len(args):
        return False
    return all(_validate_type(v, t) for v, t in zip(value, args))


def _validate_maybe(value: Any, origin: Any, args: tuple) -> bool:
    if not isinstance(value, origin):
        return False

    return value.value is None or _validate_type(value.value, args[0])
