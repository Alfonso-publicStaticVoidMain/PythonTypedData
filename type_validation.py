from __future__ import annotations

import collections
from types import UnionType
from typing import Iterable, Any, get_origin, get_args, Union, Annotated, Literal, Mapping

from abstract_classes import Collection, AbstractDict
from maybe import Maybe


def _validate_or_coerce_value[T](
    obj: object,
    expected_type: type[T],
    *,
    _coerce: bool = False
) -> T:
    """
    Validates or coerces an obj to match a given type.

    Always allows safe conversions:
        - int -> float
        - int, float -> complex
        - bool -> int, float
    Allows conversions from str only if _coerce=True:
        - str -> int, float, complex

    :param expected_type: Type to validate the obj for, or _coerce iterable into.
    :param obj: Value to validate or _coerce.
    :param _coerce: True if you want "unsafe" coercions to happen. Defaulted to False.
    :returns: The obj itself if iterable's of the expected type, or its coercion to that type if that is safe or manually
    enabled via the _coerce parameter, and iterable can be performed.
    :raises: TypeError if obj doesn't match expected_type and cannot be safely coerced.
    """
    if _validate_type(obj, expected_type):
        return obj

    # *********** Always-safe coercions ***********
    if expected_type is float and isinstance(obj, (int, bool)):
        return float(obj)  # int | bool -> float

    if expected_type is int and isinstance(obj, bool):
        return int(obj)  # bool -> int

    if expected_type is complex and isinstance(obj, (int, float, bool)):
        return complex(obj)  # int | float | bool -> complex

    if expected_type is str and isinstance(obj, (int, float, complex, bool)):
        return str(obj)  # int | float | complex | bool -> str

    # *********** str-based coercions ***********
    if _coerce:
        if isinstance(obj, str):
            try:
                if expected_type is int:
                    return int(obj)  # str -> int

                elif expected_type is float:
                    return float(obj)  # str -> float

                elif expected_type is complex:
                    return complex(obj)  # str -> complex

            except ValueError:
                raise TypeError(f"Value {obj!r} is not of type {expected_type.__name__} and cannot be converted safely to it.")

    raise TypeError(f"Value {obj!r} is not of type {expected_type.__name__}.")


def _validate_or_coerce_iterable[T](
    iterable: Iterable[Any] | None,
    expected_type: type[T],
    *,
    _coerce: bool = False
) -> list[T]:
    """
    Validates that all elements of an Iterable are of a given type, and coerces all that aren't if the _coerce parameter
    is set to True. Returns the coerced or validated iterable as a list.
    :param expected_type: Type to _coerce the elements to.
    :param iterable: Iterable object to _coerce its elements into.
    :return: A list containing all elements after performing coercion.
    :raise: An Error will be raised if any coercion isn't possible.
    """
    if iterable is None:
        return []
    return [_validate_or_coerce_value(value, expected_type, _coerce=_coerce) for value in iterable]


def _validate_collection_type_and_get_values[T](
    collection: Iterable[T] | Collection[T],
    expected_type: type[T],
    *,
    _valid_typed_types: tuple[type[Collection], ...] = (Collection,),
    _valid_built_in_types: tuple[type[Iterable], ...] = (Iterable,),
    _coerce: bool = False) -> list[T]:
    """
    Checks that an Iterable or Collection object other holds iterable of type expected_type and that is of a given allowed
    type from among this library's typed types or Python's built-ins. Returns a list containing the values the iterable held,
    after performing type coercion if enabled.
    :param expected_type: Type to compare the type against.
    :param collection: Typed or not object to check its contained type.
    :param _valid_typed_types: Types from my typed classes that should be accepted.
    :param _valid_built_in_types: Typed from Python's built ins that should be accepted.
    :return: A list containing the iterable contained on the others object after validating its type and coercing.
    """
    if isinstance(collection, _valid_typed_types):
        if not _coerce and not issubclass(collection.item_type, expected_type):
            raise ValueError(f"Type mismatch between expected type {expected_type.__name__} and actual: {collection.item_type.__name__}")
        other_values = _validate_or_coerce_iterable(collection.values, expected_type, _coerce=_coerce)
    elif isinstance(collection, _valid_built_in_types):
        other_values = _validate_or_coerce_iterable(collection, expected_type, _coerce=_coerce)

    else:
        raise TypeError(f"{collection} must be a valid type.")

    return other_values


def _validate_or_coerce_iterable_of_iterables[T](
    iterables: Iterable[Iterable[T]],
    expected_type: type[T],
    *,
    _coerce: bool = False
) -> list[list[T]]:
    other_iterables: list = []
    for iterable in iterables:
        other_iterables.append(_validate_collection_type_and_get_values(iterable, expected_type, _coerce=_coerce))
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
        raise ValueError(f"Duplicate keys detected: {duplicates}")


def _split_keys_values[K, V](
    keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]
) -> tuple[list[K], list[V], bool]:
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
                raise TypeError(f"Expected iterable of (key, obj) tuples, got: {pair!r}")
            key, value = pair
            keys.append(key)
            values.append(value)
    else:
        raise TypeError(f"The keys_values argument must be a dict, Mapping, AbstractDict, or iterable of (key, obj) tuples.")
    if len(keys) != len(values):
        raise ValueError("The number of keys and values aren't equal.")
    return keys, values, keys_from_iterable


def _infer_type(obj: Any) -> type:
    """
    Infers the most specific typing annotation of a given obj,
    recursively handling collections like list, set, dict, and tuple.
    """
    if isinstance(obj, (list, set, frozenset)):
        return _infer_iterable_type(obj)

    elif isinstance(obj, (dict, Mapping)):
        return _infer_mapping_type(obj)

    elif isinstance(obj, tuple):
        return _infer_tuple_type(obj)

    return type(obj)


def _infer_iterable_type(iterable: Any) -> type:
    if isinstance(iterable, Collection):
        inferred = type(iterable)._inferred_item_type()
        if inferred is not None:
            return type(iterable)

        item_type = getattr(iterable, 'item_type', None)
        if item_type is not None:
            return type(iterable)[item_type]

    if not iterable:
        raise ValueError("Cannot infer type from empty iterable")

    inner_type = _combine_types({_infer_type(value) for value in iterable})

    if isinstance(iterable, (list, set, frozenset)):
        return type(iterable)[inner_type]
    else:
        return Iterable[inner_type]


def _infer_mapping_type(mapping: Mapping) -> type:
    if isinstance(mapping, AbstractDict):
        inferred_key, inferred_value = type(mapping)._inferred_key_value_types()
        if inferred_key is not None and inferred_value is not None:
            return type(mapping)

        key_type = getattr(mapping, 'key_type', None)
        value_type = getattr(mapping, 'value_type', None)
        if key_type is not None and value_type is not None:
            return type(mapping)[key_type, value_type]

    if not mapping:
        raise ValueError("Cannot infer type from empty mapping")

    key_type = _infer_type_contained_in_iterable(mapping.keys())
    value_type = _infer_type_contained_in_iterable(mapping.values())

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


def _infer_type_contained_in_iterable[T](iterable: Iterable[Any]) -> type[T]:
    """
    Infers the type of items inside an iterable by inferring the type of each item.
    Supports nested containers. Raises ValueError if the iterable is empty or contains incompatible types.
    """
    if iterable is None:
        raise ValueError("Cannot infer type from None")
    if isinstance(iterable, Collection) and hasattr(type(iterable), '_args'):
        return type(iterable)._inferred_item_type()
    if not iterable:
        raise ValueError("Cannot infer type from an empty iterable")

    return _combine_types({_infer_type(val) for val in iterable})


def _validate_type(obj: Any, expected_type: type) -> bool:
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is None and hasattr(expected_type, '_args'):
        origin = expected_type._origin
        args = expected_type._args

    if origin in (Union, UnionType):
        return any(_validate_type(obj, arg) for arg in args)

    if origin is Annotated:
        return _validate_type(obj, args[0])

    if origin is Literal:
        return obj in args

    if origin is tuple:
        return _validate_tuple(obj, args)

    if origin in (list, set, frozenset, collections.abc.Sequence) or (isinstance(origin, type) and issubclass(origin, Collection)):
        return _validate_iterable(obj, origin, args[0])

    if origin in (collections.abc.Mapping, dict) or (isinstance(origin, type) and issubclass(origin, AbstractDict)):
        return _validate_mapping(obj, origin, args)

    if isinstance(origin, type) and issubclass(origin, Maybe):
        return _validate_maybe(obj, args[0])

    if origin is None:
        return isinstance(obj, expected_type)

    return False


def _validate_iterable(obj: Any, iterable_type: type, item_type: Any) -> bool:
    if not isinstance(obj, iterable_type) or isinstance(obj, str):
        return False
    return all(_validate_type(item, item_type) for item in obj)


def _validate_mapping(obj: Any, mapping_type: type, key_value_types: tuple[type, type]) -> bool:
    if not isinstance(obj, mapping_type):
        return False
    if len(key_value_types) != 2:
        raise ValueError(f"_validate_mapping_type method called with a tuple argument {key_value_types} of length {len(key_value_types)} != 2.")
    key_type, val_type = key_value_types
    return all(_validate_type(key, key_type) and _validate_type(value, val_type) for key, value in obj.items())


def _validate_tuple(obj: Any, args: tuple) -> bool:
    if not isinstance(obj, tuple):
        return False
    if len(args) == 2 and args[1] is Ellipsis:
        return all(_validate_type(v, args[0]) for v in obj)
    if len(obj) != len(args):
        return False
    return all(_validate_type(v, t) for v, t in zip(obj, args))


def _validate_maybe(obj: Any, args: Any) -> bool:
    if not isinstance(obj, Maybe):
        return False
    return obj.value is None or _validate_type(obj.value, args)
