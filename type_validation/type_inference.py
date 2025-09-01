from __future__ import annotations

from typing import Mapping, Iterable

from abstract_classes.abstract_dict import AbstractDict
from abstract_classes.collection import Collection
from type_validation.type_hierarchy import _is_subtype

from collections import OrderedDict, defaultdict


MAPPING_TYPES = (dict, Mapping, OrderedDict, defaultdict, AbstractDict)
ATOMIC_ITERABLES = (str, bytes, bytearray, memoryview, range)


def _infer_type[T](obj: T) -> type[T]:
    """
    Infers the most specific typing annotation of a given object, recursively handling collections like list, dict, and tuple.

    :param obj: Object to infer the type of.
    :type obj: Any

    :return: The type of the object, including its generics.
    :rtype: type
    """
    if isinstance(obj, tuple):
        return _infer_tuple_type(obj)

    if isinstance(obj, MAPPING_TYPES):
        return _infer_mapping_type(obj)

    if isinstance(obj, Iterable) and not isinstance(obj, ATOMIC_ITERABLES):
        return _infer_iterable_type(obj)

    return type(obj)


def _infer_iterable_type[T](iterable: Iterable[T]) -> type[Iterable[T]]:
    """
    Infers the typing annotation of an iterable object, including its generics, which are handled recursively.

    :param iterable: Iterable to infer the type of.
    :type iterable: Iterable[T]

    :return: The type of the iterable.
    :rtype: type[T]
    """
    if callable(getattr(iterable, '_inferred_item_type', None)):
        item_type = type(iterable)._inferred_item_type()
        if item_type is not None:
            return type(iterable)

    if not iterable:
        raise ValueError("Cannot infer type from empty iterable")

    if isinstance(iterable, (str, bytes)):
        raise ValueError("Iterable is a string or bytes.")

    inner_type: type[T] = _infer_type_contained_in_iterable(iterable)

    try:
        return type(iterable)[inner_type]
    except (TypeError, AttributeError):
        return Iterable[inner_type]


def _infer_mapping_type[K, V](mapping: Mapping[K, V]) -> type[Mapping[K, V]]:
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

    if not mapping:
        raise ValueError("Cannot infer type from empty mapping")

    key_type = _infer_type_contained_in_iterable(mapping.keys())
    value_type = _infer_type_contained_in_iterable(mapping.values())

    return type(mapping)[key_type, value_type]


def _infer_tuple_type(tpl: tuple) -> type[tuple]:
    """
    Infers the typing annotation of a tuple, including its generic types, which are handled recursively.

    :param tpl: Tuple to infer the type of.
    :type tpl: tuple

    :return: The type of the tuple.
    :rtype: type
    """
    return tuple[_infer_type_contained_in_tuple(tpl)]


def _infer_type_contained_in_tuple(tpl: tuple) -> tuple[type, ...]:
    if not tpl:
        raise ValueError(f"Tuple object {tpl} was empty.")
    return tuple(_infer_type(element) for element in tpl)


def _combine_types[T](types: set[type[T]]) -> type[T]:
    """
    Combines all types contained in a set of types into a single one using the union pipe operator |.

    :param types: Set of types to combine.
    :type types: set[type[T]]

    :return: The union of all types found within the set.
    :rtype: type[T]
    """
    if not types:
        raise ValueError("Cannot combine an empty type set.")

    if len(types) == 1:
        return next(iter(types))

    result_type = None
    for t in types:
        if not _is_subtype(t, result_type):
            result_type = t if result_type is None else result_type | t
    return result_type


def _infer_type_contained_in_iterable[T](iterable: Iterable[T]) -> type[T]:
    """
    Infers the type of items inside an iterable by inferring the type of each item and combining them if needed.

    Supports nested containers and recursively infers their generic types too.

    If this method receives a generator as its iterable argument, it will consume it in order to infer its type.

    :param iterable: Iterable object to infer its contained type.
    :type iterable: Iterable[T]

    :return: A type that all the items in the iterable belong to, with unions if need be.
    :rtype: type[T]

    :raises ValueError: If the iterable is None or if it's empty but isn't a Collection (which still has an item_type
     attached even if they're empty).
    """
    if iterable is None:
        raise ValueError("Cannot infer type from None.")

    if isinstance(iterable, Collection) and hasattr(type(iterable), '_args'):
        return type(iterable)._inferred_item_type()

    if not iterable:
        raise ValueError("Cannot infer type from an empty iterable.")

    return _combine_types({_infer_type(val) for val in iterable})
