from __future__ import annotations

from types import UnionType
from typing import Iterable, Any, get_origin, get_args, Union, Annotated, Literal, Mapping, Sequence, Callable

from abstract_classes.abstract_dict import AbstractDict
from abstract_classes.collection import Collection
from concrete_classes.maybe import Maybe


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


def _validate_iterable[T](obj: Any, iterable_type: type[Iterable[T]], item_type: type[T]) -> bool:
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

    :param obj: Value to validate or coerce.
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
    _coerce: bool = False,
    _finisher: Callable[[Iterable[T]], Iterable[T]] | Callable[[], Iterable[T]] = list
) -> Iterable[T]:
    """
    Validates and optionally coerces the elements of an iterable against a given type, and returns them as a list.

    :param expected_type: Type to validate against and optionally coerce the elements into.
    :type expected_type: type[T]

    :param iterable: Iterable object to _coerce its elements into.
    :type iterable: Iterable[Any] | None

    :param _coerce: If True, attempts to coerce each value in the iterable to the expected type.
    :type _coerce: bool

    :param _finisher: Callable to be applied to the validated or coerced values before returning them.
    :type _finisher: Callable[[Iterable[T]], Iterable[T]] | Callable[[], Iterable[T]]

    :return: A list containing all elements after performing validation and optionally coercion.
    :rtype: list[T]

    :raises TypeError: If any value isn't of the expected type and coercion isn't possible or wasn't enabled.
    """
    if iterable is None:
        return _finisher()
    return _finisher(_validate_or_coerce_value(value, expected_type, _coerce=_coerce) for value in iterable)


def _validate_or_coerce_iterable_of_iterables[T](
    iterables: Iterable[Iterable[T]],
    expected_type: type[T],
    *,
    _coerce: bool = False,
    _inner_finisher: Callable[[Iterable[T]], Iterable[T]] = set,
    _outer_finisher: Callable[[Iterable[T]], Iterable[T]] = tuple
) -> Iterable[Iterable[T]]:
    """
    Validates and optionally coerces each iterable inside an iterable and returns them as a list of lists.

    :param iterables: An Iterable containing one or more Iterable objects to validate and coerce.
    :type iterables: Iterable[Iterable[T]]

    :param expected_type: Type to validate against and optionally coerce the values into.
    :type expected_type: type[T]

    :param _coerce: State parameter to force type coercion or not. Some numeric type coercions are always performed.
    :type _coerce: bool

    :param _inner_finisher: Callable to apply to each Iterable as they're added to the Iterable that'll be returned.
    :type _inner_finisher: Callable[[Iterable[T]], Iterable[T]]

    :param _outer_finisher: Callable to apply to the returned final Iterable of Iterables.
    :type _outer_finisher: Callable[[Iterable[T]], Iterable[T]]

    :return: A list of lists containing the validated and optionally coerced iterables.
    :rtype: list[list[T]]
    """
    other_iterables: list = []
    for iterable in iterables:
        other_iterables.append(_validate_or_coerce_iterable(iterable, expected_type, _coerce=_coerce, _finisher=_inner_finisher))
    return _outer_finisher(other_iterables)


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
