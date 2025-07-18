from __future__ import annotations

import collections
import types
from typing import Iterable, Any, get_origin, get_args, Union, Annotated, Literal, Mapping

from abstract_classes import Collection, AbstractDict
from maybe import Maybe


def _validate_or_coerce_value[T](
    expected_type: type[T],
    value: object,
    coerce: bool = False
) -> T:
    """
    Validates or coerces a value to match a given type.

    Always allows safe conversions:
        - int -> float
        - int, float -> complex
        - bool -> int, float
    Allows conversions from str only if _coerce=True:
        - str -> int, float, complex

    :param expected_type: Type to validate the value for, or _coerce iterable into.
    :param value: Value to validate or _coerce.
    :param coerce: True if you want "unsafe" coercions to happen. Defaulted to False.
    :returns: The value itself if iterable's of the expected type, or its coercion to that type if that is safe or manually
    enabled via the _coerce parameter, and iterable can be performed.
    :raises: TypeError if value doesn't match expected_type and cannot be safely coerced.
    """
    if _validate_type(value, expected_type):
        return value

    # === Always-safe coercions ===
    if expected_type is float and isinstance(value, (int, bool)):
        return float(value) # int | bool -> float

    if expected_type is int and isinstance(value, bool):
        return int(value) # bool -> int

    if expected_type is complex and isinstance(value, (int, float, bool)):
        return complex(value) # int | float | bool -> complex

    if expected_type is str and isinstance(value, (int, float, complex, bool)):
        return str(value) # int | float | complex | bool -> str

    # === str-based coercions ===
    if coerce:
        if isinstance(value, str):
            try:
                if expected_type is int:
                    return int(value)  # str -> int

                elif expected_type is float:
                    return float(value)  # str -> float

                elif expected_type is complex:
                    return complex(value)  # str -> complex

            except ValueError:
                raise TypeError(f"Value {value!r} is not of type {expected_type.__name__} and cannot be converted safely to iterable.")

    raise TypeError(f"Value {value!r} is not of type {expected_type.__name__}.")


def _validate_or_coerce_iterable[T](
    item_type: type[T],
    values: Iterable[Any] | None,
    coerce: bool = False
) -> list[T]:
    """
    Validates that all elements of an Iterable are of a given type, and coerces all that aren't if the _coerce parameter
    is set to True. Returns the coerced or validated iterable as a list.
    :param item_type: Type to _coerce the elements to.
    :param values: Iterable object to _coerce its elements into.
    :return: A list containing all elements after performing coercion.
    :raise: An Error will be raised if any coercion isn't possible.
    """
    if values is None:
        return []
    return [_validate_or_coerce_value(item_type, value, coerce) for value in values]


def _validate_collection_type_and_get_values[T](
    item_type: type[T],
    other: Iterable[T] | Collection[T],
    valid_typed_types: tuple[type[Collection], ...] = (Collection,),
    valid_built_in_types: tuple[type, ...] = (Iterable,),
    coerce: bool = False
) -> list[T]:
    """
    Checks that an Iterable or Collection object other holds values of type item_type and that is of a given allowed
    type from among this library's typed types or Python's built-ins. Returns a list containing the values iterable held,
    after performing type coercion if enabled.
    :param item_type: Type to compare the type against.
    :param other: Typed or not object to check its contained type.
    :param valid_typed_types: Types from my typed classes that should be accepted.
    :param valid_built_in_types: Typed from Python's built ins that should be accepted.
    :return: A list containing the values contained on the others object after validating its type and coercing.
    """
    if isinstance(other, valid_typed_types):
        if not coerce and not issubclass(other.item_type, item_type):
            raise ValueError(f"Type mismatch between expected type {item_type.__name__} and actual: {other.item_type.__name__}")
        other_values = _validate_or_coerce_iterable(item_type, other.values, coerce)
    elif isinstance(other, valid_built_in_types):
        other_values = _validate_or_coerce_iterable(item_type, other, coerce)

    else:
        raise TypeError(f"{other} must be a valid type.")

    return other_values


def _validate_iterable_of_iterables_and_get[T](
    item_type: type[T],
    others: Iterable[Iterable[T]],
    coerce: bool = False
) -> list[list[T]]:
    from abstract_classes import Collection
    other_iterables: list = []
    for iterable in others:
        other_iterables.append(_validate_collection_type_and_get_values(item_type, iterable, (Collection,), (Iterable,), coerce))
    return other_iterables


def _validate_duplicates_and_hash(iterable: Iterable) -> None:
    seen = set()
    duplicates = set()
    for key in iterable:
        try:
            hash(key)
        except TypeError:
            raise TypeError(f"Key {key!r} is not hashable and cannot be used as a dictionary key.")
        if key in seen:
            duplicates.add(key)
        else:
            seen.add(key)
    if duplicates:
        raise ValueError(f"Duplicate keys after coercion detected: {duplicates}")


def _split_keys_values[K, V](keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]) -> tuple[list[K], list[V], bool]:
    keys_from_iterable = False
    if isinstance(keys_values, (dict, Mapping, AbstractDict)):
        keys = keys_values.keys()
        values = keys_values.values()
    elif isinstance(keys_values, Iterable):
        keys = []
        values = []
        keys_from_iterable = True
        for pair in keys_values:
            if not (isinstance(pair, tuple) and len(pair) == 2):
                raise TypeError(f"Expected iterable of (key, value) tuples, got: {pair!r}")
            key, value = pair
            keys.append(key)
            values.append(value)
    else:
        raise TypeError(f"The keys_values argument must be a dict, Mapping, AbstractDict, or iterable of (key, value) tuples.")
    if len(keys) != len(values):
        raise ValueError("The number of keys and values aren't equal.")
    return keys, values, keys_from_iterable


def _infer_type(value: Any) -> type:
    """
    Infers the most specific typing annotation of a given value,
    recursively handling collections like list, set, dict, and tuple.
    """
    if isinstance(value, (list, set, frozenset)) or isinstance(value, Collection):
        return _infer_iterable_type(value)

    elif isinstance(value, (dict, Mapping)) or isinstance(value, AbstractDict):
        return _infer_mapping_type(value)

    elif isinstance(value, tuple):
        return _infer_tuple_type(value)

    return type(value)


def _infer_iterable_type(iterable: Any) -> type:
    if isinstance(iterable, Collection):
        item_type = getattr(iterable, 'item_type', None) or getattr(type(iterable), '_inferred_item_type', None)
        if item_type is not None:
            return type(iterable)[item_type]

    if not iterable:
        raise ValueError("Cannot infer type from empty iterable")

    inner_type = _combine_types({_infer_type(v) for v in iterable})

    if isinstance(iterable, (list, set, frozenset)):
        return type(iterable)[inner_type]
    else:
        return Iterable[inner_type]


def _infer_mapping_type(mapping: Mapping) -> type:
    if isinstance(mapping, AbstractDict):
        key_type = getattr(mapping, 'key_type', None) or getattr(type(mapping), '_inferred_key_type', None)
        value_type = getattr(mapping, 'value_type', None) or getattr(type(mapping), '_inferred_value_type', None)
        if key_type and value_type:
            return type(mapping)[key_type, value_type]

    if not mapping:
        raise ValueError("Cannot infer type from empty mapping")

    key_type = _infer_type_contained_in_iterable(mapping.keys())
    value_type =_infer_type_contained_in_iterable(mapping.values())

    return type(mapping)[key_type, value_type]


def _infer_tuple_type(tpl: tuple) -> type:
    if not tpl:
        return tuple[()]
    element_types = tuple(_infer_type(element) for element in tpl)
    return tuple[element_types]


def _combine_types[T](type_set: set[type[T]]) -> type[T]:
    if not type_set:
        raise ValueError("Cannot combine empty type set")
    elif len(type_set) == 1:
        return next(iter(type_set))
    else:
        result_type = None
        for t in type_set:
            result_type = t if result_type is None else result_type | t
        return result_type


def _infer_type_contained_in_iterable[T](values: Iterable[Any]) -> type[T]:
    """
    Infers the type of items inside an iterable by inferring the type of each item.
    Supports nested containers. Raises ValueError if the iterable is empty or contains incompatible types.
    """
    if values is None:
        raise ValueError("Cannot infer type from None")
    if not values:
        raise ValueError("Cannot infer type from an empty iterable")

    return _combine_types({_infer_type(val) for val in values})


def _validate_type(value: Any, expected_type: type) -> bool:
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is None:
        if hasattr(expected_type, '_inferred_item_type'):
            origin = expected_type
            args = (getattr(expected_type, '_inferred_item_type'),)
        elif hasattr(expected_type, '_inferred_key_type') and hasattr(expected_type, '_inferred_value_type'):
            origin = expected_type
            args = (
                getattr(expected_type, '_inferred_key_type'),
                getattr(expected_type, '_inferred_value_type')
            )

    if origin in (Union, types.UnionType):
        return any(_validate_type(value, arg) for arg in args)

    if origin is Annotated:
        return _validate_type(value, args[0])

    if origin is Literal:
        return value in args

    if origin is tuple:
        return _validate_tuple(value, args)

    if origin in (list, set, frozenset, collections.abc.Sequence) or (isinstance(origin, type) and issubclass(origin, Collection)):
        return _validate_iterable(value, origin, args[0])

    if origin in (collections.abc.Mapping, dict) or (isinstance(origin, type) and issubclass(origin, AbstractDict)):
        return _validate_mapping_type(value, origin, args)

    if origin is Maybe:
        return _validate_maybe(value, origin, args)

    if origin is None:
        return isinstance(value, expected_type)

    return False


def _validate_type_of_iterable(expected_type: type, values: Iterable[Any]) -> bool:
    return all([_validate_type(value, expected_type) for value in values])


def _validate_iterable(value: Any, iterable_type: type, item_type: Any) -> bool:
    if not isinstance(value, iterable_type) or isinstance(value, str):
        return False
    return all(_validate_type(v, item_type) for v in value)


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
