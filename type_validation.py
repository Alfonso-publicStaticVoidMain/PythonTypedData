from __future__ import annotations

from types import UnionType
from typing import Iterable, Any, get_origin, get_args, Union, Annotated, Literal, Mapping, Sequence

from abstract_classes import Collection, AbstractDict
from maybe import Maybe


def _validate_type(obj: Any, expected_type: type) -> bool:
    """
    Validates if an object is of an expected type, with matching generics.

    :param obj: Object to validate the type of.
    :type obj: Any

    :param expected_type: Type to check if the object is an instance of.
    :type expected_type: type

    :return: True if the object is an instance of the expected type, matching its generics too. False otherwise.
    :rtype: bool
    """
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

    if origin in (list, set, frozenset, Sequence) or (isinstance(origin, type) and issubclass(origin, Collection)):
        return _validate_iterable(obj, origin, args[0])

    if origin in (Mapping, dict) or (isinstance(origin, type) and issubclass(origin, AbstractDict)):
        return _validate_mapping(obj, origin, args)

    if isinstance(origin, type) and issubclass(origin, Maybe):
        return _validate_maybe(obj, args[0])

    if origin is None:
        return isinstance(obj, expected_type)

    return False


def _validate_iterable(obj: Any, iterable_type: type, item_type: type) -> bool:
    """
    Validates that all items in an iterable are of the expected type.

    :param obj: Iterable object whose items to validate.
    :type obj: Any

    :param item_type: Type to validate the items against.
    :type item_type: type

    :return: True if all elements of the iterable validate the given type, False otherwise or if the object isn't an
    Iterable.
    :rtype: bool
    """
    if not isinstance(obj, iterable_type) or isinstance(obj, str):
        return False
    return all(_validate_type(item, item_type) for item in obj)


def _validate_mapping(obj: Any, mapping_type: type, key_value_types: tuple[type, type]) -> bool:
    """
    Validates that all keys and values of a mapping match their expected key and value type.

    :param obj: Mapping object whose keys and values to validate.
    :type obj: Any

    :param key_value_types: Tuple of key type and value type expected of the Mapping's keys and values.
    :type key_value_types: tuple[type, type]

    :return: True if all keys and all values validate their given type, False otherwise or if the object isn't a
    Mapping or AbstractDict.
    :rtype: bool

    :raises ValueError: If the key_value_types tuple parameter isn't of length 2.
    """
    if not isinstance(obj, mapping_type):
        return False
    if len(key_value_types) != 2:
        raise ValueError(f"_validate_mapping_type method called with a tuple argument {key_value_types} of length {len(key_value_types)} != 2.")
    key_type, val_type = key_value_types
    return all(_validate_type(key, key_type) and _validate_type(value, val_type) for key, value in obj.items())


def _validate_tuple(obj: Any, args: tuple) -> bool:
    """
    Validates that a tuple matches the given args.

    :param obj: Tuple object to validate.
    :type obj: Any

    :param args: Tuple containing the types expected on the tuple.
    :type args: tuple

    :return: True if the tuple object validates the types contained on args, accounting for possible Ellipsis, False
    otherwise or if the object isn't a tuple.
    :rtype: bool
    """
    if not isinstance(obj, tuple):
        return False
    if len(args) == 2 and args[1] is Ellipsis:
        return all(_validate_type(v, args[0]) for v in obj)
    if len(obj) != len(args):
        return False
    return all(_validate_type(v, t) for v, t in zip(obj, args))


def _validate_maybe(obj: Any, args: Any) -> bool:
    """
    Validates that a Maybe object is set up to contain a value of type args.

    :param obj: Maybe object to validate.
    :type obj: Any

    :param args: Type expected to be contained on the object,
    :type args: Any

    :return: True if obj is an instance of Maybe, its item_type is args and either its value is None or is of type args.
    False otherwise.
    :rtype: bool
    """
    if not isinstance(obj, Maybe):
        return False
    return obj.item_type == args and (obj.value is None or _validate_type(obj.value, args))


def _validate_or_coerce_value[T](
    obj: object,
    expected_type: type[T],
    *,
    _coerce: bool = False
) -> T:
    """
    Validates or coerces an object to match a given type, then returns it.

    Always allows safe conversions:
        - int -> float
        - int, float -> complex
        - bool -> int, float
        - bool, int, float, complex -> str
    And if _coerce=True:
        - str -> int, float, complex

    :param obj: Value to validate or _coerce.
    :type obj: object

    :param expected_type: Type to validate the obj for, or _coerce iterable into.
    :type expected_type: type[T]

    :param _coerce: True if you want "unsafe" coercions to happen. Defaulted to False.
    :type _coerce: bool

    :returns: The obj itself if it's of the expected type, or its coercion to that type if it's valid.
    :rtype: T

    :raises TypeError: if obj doesn't match item_type and cannot be safely coerced.
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
    Validates and optionally coerces the elements of an iterable against a given type, and returns them as a list.

    :param expected_type: Type to validate against and optionally coerce the elements into.
    :type expected_type: type[T]

    :param iterable: Iterable object to _coerce its elements into.
    :type iterable: Iterable[Any] | None

    :return: A list containing all elements after performing validation and optionally coercion.
    :rtype: list[T]

    :raises TypeError: If any value isn't of the expected type and coercion isn't possible or wasn't enabled.
    """
    if iterable is None:
        return []
    return [_validate_or_coerce_value(value, expected_type, _coerce=_coerce) for value in iterable]

def _validate_or_coerce_tuple(
        tpl: tuple,
        # TODO
):
    pass

def _validate_collection_type_and_get_values[T](
    collection: Iterable[T] | Collection[T],
    expected_type: type[T],
    *,
    _valid_typed_types: tuple[type[Collection], ...] = (Collection,),
    _valid_built_in_types: tuple[type[Iterable], ...] = (Iterable,),
    _coerce: bool = False
) -> list[T]:
    """
    Validates and optionally coerces the elements, also checking that the Iterable is of one of the given allowed types.

    Checks that an Iterable or Collection object other holds values of type item_type and that is of a given allowed
    type from among this library's typed types or Python's built-ins. Returns a list containing the values the iterable
    held, after performing type coercion if enabled.

    :param collection: Typed or not object to check its contained type.
    :type collection: Iterable[T] | Collection[T]

    :param expected_type: Type to compare the type against.
    :type expected_type: type[T]

    :param _valid_typed_types: Types from this library that should be accepted.
    :type _valid_typed_types: tuple[type[Collection], ...]

    :param _valid_built_in_types: Typed from Python's built ins that should be accepted.
    :type _valid_built_in_types: tuple[type[Iterable], ...]

    :return: A list with the values of the iterable after validation and coercion.
    :rtype: list[T]
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
    """
    Validates and optionally coerces each iterable inside an iterable and returns them as a list of lists.

    :param iterables: An Iterable containing one or more Iterable objects to validate and coerce.
    :type iterables: Iterable[Iterable[T]]

    :param expected_type: Type to validate against and optionally coerce the values into.
    :type expected_type: type[T]

    :param _coerce: State parameter to force type coercion or not. Some numeric type coercions are always performed.
    :type _coerce: bool

    :return: A list of lists containing the validated and optionally coerced iterables.
    :rtype: list[list[T]]
    """
    other_iterables: list = []
    for iterable in iterables:
        other_iterables.append(_validate_collection_type_and_get_values(iterable, expected_type, _coerce=_coerce))
    return other_iterables


def _validate_duplicates_and_hash(iterable: Iterable) -> None:
    """
    Validates that an iterable contains only hashable elements and no duplicates. Raises an Error otherwise.

    :param iterable: Iterable object to validate.
    :type iterable: Iterable

    :raises TypeError: If the iterable contains a key that isn't hashable.
    :raises ValueError: If the iterable contains duplicate elements, and displays those.
    """
    seen = set()
    duplicates = set()
    for key in iterable:
        if key in seen:
            duplicates.add(key)
        else:
            try:
                seen.add(key)
            except TypeError:
                raise TypeError(f"Key {key!r} is not hashable and cannot be used as a dictionary key.")
    if duplicates:
        raise ValueError(f"Duplicate keys detected: {duplicates}")


def _split_keys_values[K, V](keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]) -> tuple[list[K], list[V], bool]:
    """
    Splits the keys and values from a dict-like structure or an iterable of (key, value) tuples and returns them.

    :param keys_values: Data structure containing the keys and values.
    :type keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]

    :return: A tuple of the list of keys, the list of values, and a boolean that will be True if they came from an
    iterable of tuples.
    :rtype: tuple[list[K], list[V], bool]

    :raises TypeError: If the keys and values were given as an iterable but it either doesn't contain tuples or any
    of those tuples isn't of length 2.
    :raises TypeError: If the keys_values parameter isn't of the allowed types.
    :raises ValueError: If the number of keys and values differ.
    """
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
    Infers the most specific typing annotation of a given object, recursively handling collections like list, dict, and tuple.

    :param obj: Object to infer the type of.
    :type obj: Any

    :return: The type of the object, including its generics.
    :rtype: type
    """
    if isinstance(obj, (list, set, frozenset)):
        return _infer_iterable_type(obj)

    elif isinstance(obj, (dict, Mapping)):
        return _infer_mapping_type(obj)

    elif isinstance(obj, tuple):
        return _infer_tuple_type(obj)

    return type(obj)


def _infer_iterable_type(iterable: Iterable) -> type:
    """
    Infers the typing annotation of an iterable object, including its generics, which are handled recursively.

    :param iterable: Iterable to infer the type of.
    :type iterable: Iterable

    :return: The type of the iterable.
    :rtype: type
    """
    if isinstance(iterable, Collection):
        if hasattr(type(iterable), '_args'):
            return type(iterable)
        return type(iterable)[iterable.item_type]

    if not iterable:
        raise ValueError("Cannot infer type from empty iterable")

    inner_type = _combine_types({_infer_type(value) for value in iterable})

    if isinstance(iterable, (list, set, frozenset)):
        return type(iterable)[inner_type]
    else:
        return Iterable[inner_type]


def _infer_mapping_type(mapping: Mapping) -> type:
    """
    Infers the typing annotation of a mapping object, including its generics, which are handled recursively.

    :param mapping: Mapping to infer the type of.
    :type mapping: Mapping

    :return: The type of the mapping.
    :rtype: type
    """
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
    """
    Infers the typing annotation of a tuple, including its generic types, which are handled recursively.

    :param tpl: Tuple to infer the type of.
    :type tpl: tuple

    :return: The type of the tuple.
    :rtype: type
    """
    if not tpl:
        return tuple[()]
    element_types = tuple(_infer_type(element) for element in tpl)
    return tuple[element_types]


def _combine_types[T](type_set: set[type[T]]) -> type[T]:
    """
    Combines all types contained in a set of types into a single one using the union pipe operator |.

    :param type_set: Set of types to combine.
    :type type_set: set[type[T]]

    :return: The union of all types found within the set.
    :rtype: type[T]
    """
    if not type_set:
        raise ValueError("Cannot combine an empty type set")
    elif len(type_set) == 1:
        return next(iter(type_set))
    else:
        result_type = None
        for t in type_set:
            result_type = t if result_type is None else result_type | t
        return result_type


def _infer_type_contained_in_iterable[T](iterable: Iterable[T]) -> type[T]:
    """
    Infers the type of items inside an iterable by inferring the type of each item and combining them if needed.

    Supports nested containers and recursively infers their generic types too.

    :param iterable: Iterable object to infer its contained type.
    :type iterable: Iterable[T]

    :return: A type that all the items in the iterable belong to, with unions if need be.
    :rtype: type[T]

    :raises ValueError: If the iterable is None or if it's empty but isn't a Collection (which still has an item_type
    attached even if they're empty).
    """
    if iterable is None:
        raise ValueError("Cannot infer type from None")

    if isinstance(iterable, Collection) and hasattr(type(iterable), '_args'):
        return type(iterable)._inferred_item_type()

    if not iterable:
        raise ValueError("Cannot infer type from an empty iterable")

    return _combine_types({_infer_type(val) for val in iterable})
