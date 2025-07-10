from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar, Generic, Iterator, Callable, Any, Iterable, ClassVar

import frozendict

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")


def _validate_value(value: object, item_type: type) -> object:
    """
    Checks if a single value is of a given type, or if it can be safely converted to that type. Valid conversions for
    now are int -> float, str -> (int, float) and Any -> str provided no error is raised.
    :param value: Value to check validity of.
    :param item_type: Type to check match for the value.
    :return: The value itself if it's of type item_type, or its conversion to item_type if it can safely converted to it.
    :raise: TypeError if the value isn't of item_type and can't be safely converted to it.
    """
    if isinstance(value, item_type):
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


def _validate_values(actual_values: Iterable, item_type: type) -> list:
    """
    Checks if all elements of the given Iterable are of the given type or a subclass thereof. If not, raises a TypeError.
    :param actual_values: Iterable of values of possibly different types.
    :param item_type: Type to check for.
    :raise: TypeError if not all elements of the actual_values list are of type item_type.
    """
    validated_values = []
    for value in actual_values:
        validated_values.append(_validate_value(value, item_type))
    return validated_values


def _validate_types(self, other, valid_typed_types: tuple[type, ...], valid_built_in_types: tuple[type, ...]) -> list:
    """
    Checks that two objects self and other hold compatible types. Self will always be assumed a typed class, while other
    will be of the parameter tuples valid_typed_typed and valid_built_in_types.
    :param self: Typed object to compare the type against.
    :param other: Typed or not object to check its contained type.
    :param valid_typed_types: Types from my typed classes that should be accepted.
    :param valid_built_in_types: Typed from Python's built ins that should be accepted.
    :return: A list containing the values contained on the other object after validating its type and converting it to
    self.item_type if necessary.
    """
    if isinstance(other, valid_typed_types):
        if not issubclass(other.item_type, self.item_type):
            raise ValueError(f"Different types for self ({self.item_type.__name__}) and other ({other.item_type.__name__})")
        other_values = other.values
    elif isinstance(other, valid_built_in_types):
        other_values = _validate_values(other, self.item_type)
    else:
        raise TypeError(f"{other} must be a valid type.")
    return other_values


def functional_methods(cls):

    def map(self, f: Callable[[T], U]):
        mapped = [f(v) for v in self.values]
        item_type = type(mapped[0]) if mapped else object
        return self.__class__(item_type, mapped)

    def flatmap(self, f: Callable[[T], Iterable[U]]):
        flattened = []
        for v in self.values:
            result = f(v)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        return self.__class__(type(flattened[0]) if flattened else object, flattened)

    def filter(self, pred: Callable[[T], bool]):
        return self.__class__(self.item_type, [v for v in self.values if pred(v)])

    def all_match(self, pred: Callable[[T], bool]) -> bool:
        return all(pred(v) for v in self.values)

    def any_match(self, pred: Callable[[T], bool]) -> bool:
        return any(pred(v) for v in self.values)

    def none_match(self, pred: Callable[[T], bool]) -> bool:
        return not any(pred(v) for v in self.values)

    for name, func in locals().items():
        if callable(func):
            setattr(cls, name, func)

    return cls


def shared_container_methods(cls):

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def __contains__(self, item):
        return item in self.values

    def __eq__(self, other):
        return (
            isinstance(other, cls)
            and self.item_type == other.item_type
            and self.values == other.values
        )

    def __repr__(self):
        return f"{cls.__name__}<{self.item_type.__name__}>{self.values}"

    def __bool__(self):
        return bool(self.values)

    def copy(self):
        return cls(self.item_type, self.values.copy() if hasattr(self.values, 'copy') else self.values)

    def to_list(self):
        return list(self.values)

    def to_tuple(self):
        return tuple(self.values)

    def to_set(self):
        return set(self.values)

    def to_frozen_set(self):
        return frozenset(self.values)

    def count(self, value):
        try:
            return self.values.count(value)
        except AttributeError:
            return sum(1 for v in self.values if v == value)

    for name, func in locals().items():
        if callable(func):
            setattr(cls, name, func)

    return cls


def shared_sequence_methods(cls):

    def __getitem__(self, index: int | slice):
        if isinstance(index, slice):
            return cls(self.item_type, self.values[index])
        elif isinstance(index, int):
            return self.values[index]
        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __lt__(self, other):
        if isinstance(other, (cls, list, tuple)):
            return tuple(self.values) < tuple(other.values if isinstance(other, cls) else other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, (cls, list, tuple)):
            return tuple(self.values) > tuple(other.values if isinstance(other, cls) else other)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, (cls, list, tuple)):
            return tuple(self.values) <= tuple(other.values if isinstance(other, cls) else other)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, (cls, list, tuple)):
            return tuple(self.values) >= tuple(other.values if isinstance(other, cls) else other)
        return NotImplemented

    def __add__(self, other):
        return cls(self.item_type, self.values + _validate_types(self, other, (TypedList, TypedTuple), (list, tuple)))

    def __mul__(self, n):
        if not isinstance(n, int):
            return NotImplemented
        return cls(self.item_type, self.values * n)

    def __sub__(self, other):
        other_values = _validate_types(self, other, (TypedList, TypedTuple), (list, tuple))
        filtered_values = [value for value in self.values if value not in other_values]
        return cls(self.item_type, filtered_values)

    def __reversed__(self):
        return reversed(self.values)

    def index(self, value):
        return self.values.index(value)

    def sorted(self, key=None, reverse=False):
        return cls(self.item_type, sorted(self.values, key=key, reverse=reverse))

    for name, func in locals().items():
        if callable(func) and (not name.startswith("_") or (name.startswith("__") and name.endswith("__"))):
            setattr(cls, name, func)

    return cls


def shared_set_methods(cls):

    set_operations_names = {
        "union": set.union,
        "intersection": set.intersection,
        "difference": set.difference,
        "symmetric_difference": set.symmetric_difference,
        "is_subset": set.issubset,
        "is_superset": set.issuperset,
        "is_disjoint": set.isdisjoint,
    }

    for name, operation in set_operations_names.items():
        if name.startswith("is_"):
            # Boolean-returning methods
            def method(self, other, _op=operation):
                other_values = _validate_types(other, self, (TypedSet, TypedFrozenSet), (set, frozenset))
                return _op(self.values, other_values)
        else:
            # Set-returning methods
            def method(self, other, _op=operation):
                other_values = _validate_types(other, self, (TypedSet, TypedFrozenSet), (set, frozenset))
                return cls(self.item_type, _op(self.values, other_values))
        setattr(cls, name, method)

    return cls


def shared_dict_methods(cls):

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.data()

    def __len__(self):
        return len(self.data)

    def __contains__(self, key):
        return key in self.data

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented
        return (
            self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def copy(self):
        return cls(self.key_type, self.value_type, self.data.copy())

    def get(self, key, fallback=None):
        return self.data.get(key, fallback)

    def map_values(self, f):
        new_data = {k : f(v) for k, v in self.data.data()}
        new_value_type = type(next(iter(new_data.values()), object))
        return cls(self.key_type, new_value_type, new_data)

    def filter_items(self, predicate):
        filtered = {k : v for k, v in self.data.data() if predicate(k, v)}
        return cls(self.key_type, self.value_type, filtered)

    def subdict(self, start, end):
        try:
            if start > end:
                raise TypeError("Start must be lower than end.")
        except TypeError:
            raise TypeError("Keys must support ordering for subdict slicing.")

        sliced = {k : v for k, v in self.data.data() if start <= k <= end}
        return cls(self.key_type, self.value_type, sliced)

    for name, func in locals().items():
        if callable(func):
            setattr(cls, name, func)

    return cls


@shared_container_methods
@shared_sequence_methods
@functional_methods
@dataclass(slots=True)
class TypedList(Generic[T]):
    item_type: type[T]
    values: list[T] = field(default_factory=list)

    def __init__(self, item_type: type[T], values: Iterable[T] | None = None):
        if isinstance(values, (set, frozenset, TypedSet, TypedFrozenSet)):
            raise TypeError("TypedList does not accept a set or frozenset because their order is not guaranteed")
        self.item_type = item_type
        self.values = _validate_values(list(values) if values is not None else (), item_type)

    def append(self: TypedList[T], value: T) -> None:
        self.values.append(_validate_value(value, self.item_type))

    def __setitem__(self: TypedList[T], index: int | slice, value: T | TypedList[T] | TypedTuple[T] | list[T] | tuple[T]) -> None:
        if isinstance(index, slice):
            self.values[index] = _validate_types(self, value, (TypedList, TypedTuple), (list, tuple))

        elif isinstance(index, int):
            self.values[index] = _validate_value(value, self.item_type)

        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __delitem__(self: TypedList[T], index: int | slice) -> None:
        del self.values[index]

    def sort(self: TypedList[T], key: Callable[[T], Any] | None = None, reverse: bool = False) -> None:
        self.values.sort(key=key, reverse=reverse)


@shared_container_methods
@shared_sequence_methods
@functional_methods
@dataclass(frozen=True, slots=True)
class TypedTuple(Generic[T]):
    item_type: type[T]
    values: tuple[T, ...] = field(default_factory=tuple)

    def __init__(self, item_type: type[T], values: Iterable[T] = ()):
        if isinstance(values, (set, frozenset)):
            raise TypeError("StaticTuple does not accept set or frozenset because their order is not guaranteed")
        actual_values = tuple(values)
        _validate_values(actual_values, item_type)
        object.__setattr__(self, 'item_type', item_type)
        object.__setattr__(self, 'values', actual_values)


@shared_dict_methods
@dataclass(slots=True)
class TypedDict(Generic[K, V]):
    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __init__(
        self: TypedDict[K, V],
        key_type: type[K],
        value_type: type[V],
        keys_values: dict | frozendict | Iterable[tuple[K, V]] | None = None
    ) -> None:
        self.key_type = key_type
        self.value_type = value_type
        actual_dict = self.data = {}

        if keys_values is None:
            return

        if isinstance(keys_values, Iterable):
            keys = [key for (key, _) in keys_values]
            values = [value for (_, value) in keys_values]
        elif isinstance(keys_values, (dict, frozendict)):
            keys = list(keys_values.keys())
            values = list(keys_values.values())
        else:
            raise TypeError(f"The values aren't a dict or Iterable.")

        if len(keys) != len(values):
            raise ValueError(f"The number of keys and values aren't equal.")

        actual_keys = _validate_values(keys, key_type)
        actual_values = _validate_values(values, value_type)

        for key, value in zip(actual_keys, actual_values):
            actual_dict[key] = value

    def __setitem__(self: TypedDict[K, V], key: K, value: V) -> None:
        if not isinstance(key, self.key_type):
            raise TypeError(f"Key must be of type {self.key_type.__name__}")
        if not isinstance(value, self.value_type):
            raise TypeError(f"Value must be of type {self.value_type.__name__}")
        self.data[key] = value

    def __delitem__(self: TypedDict[K, V], key: K) -> None:
        del self.data[key]

    def clear(self: TypedDict[K, V]) -> None:
        self.data.clear()

    def update(self: TypedDict[K, V], other: dict[K, V] | TypedDict[K, V]) -> None:
        if isinstance(other, TypedDict):
            if not issubclass(other.key_type, self.key_type):
                raise TypeError(f"Cannot update with StaticDict of keys {other.key_type.__name__}")
            if not issubclass(other.value_type, self.value_type):
                raise TypeError(f"Cannot update with StaticDict of values {other.value_type.__name__}")
            other_items = other.data.items()

        elif isinstance(other, dict):
            _validate_values(other.keys(), self.key_type)
            _validate_values(other.values(), self.value_type)
            other_items = other.items()

        else:
            raise TypeError("'other' argument must be dict or StaticDict")

        for k, v in other_items:
            self[k] = v

    def map_values(self: TypedDict[K, V], f: Callable[[V], U]) -> 'TypedDict[K, U]':
        new_items = {k: f(v) for k, v in self.data.items()}
        return TypedDict(self.key_type, type(next(iter(new_items.values()), object)), new_items)

    def filter_items(self: TypedDict[K, V], predicate: Callable[[K, V], bool]) -> 'TypedDict[K, V]':
        filtered = {k: v for k, v in self.data.items() if predicate(k, v)}
        return TypedDict(self.key_type, self.value_type, filtered)

    def subdict(self: TypedDict[K, V], start: K, end: K) -> TypedDict[K, V]:
        """
        Return a new StaticDict containing items with keys k where start <= k <= end,
        assuming keys are ordered.
        """

        validate: bool = True
        try:
            validate = start <= end
        except TypeError:
            raise TypeError("Keys must support ordering for subdict slicing.")

        if not validate:
            raise TypeError("Start must be lower than end.")

        new_items = {k: v for k, v in self.data.items() if start <= k <= end}
        return TypedDict(self.key_type, self.value_type, new_items)


@shared_dict_methods
@dataclass(frozen=True, slots=True)
class TypedFrozenDict(Generic[K, V]):
    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __init__(
            self: TypedDict[K, V],
            key_type: type[K],
            value_type: type[V],
            keys_values: dict | frozendict | Iterable[tuple[K, V]] | None = None
    ) -> None:
        object.__setattr__(self, "key_type", key_type)
        object.__setattr__(self, "value_type", value_type)
        object.__setattr__(self, "data", {})

        actual_dict = self.data

        if keys_values is None:
            return

        if isinstance(keys_values, Iterable):
            keys = [key for (key, _) in keys_values]
            values = [value for (_, value) in keys_values]
        elif isinstance(keys_values, (dict, frozendict)):
            keys = list(keys_values.keys())
            values = list(keys_values.values())
        else:
            raise TypeError(f"The values aren't a dict or Iterable.")

        if len(keys) != len(values):
            raise ValueError(f"The number of keys and values aren't equal.")

        actual_keys = _validate_values(keys, key_type)
        actual_values = _validate_values(values, value_type)

        for key, value in zip(actual_keys, actual_values):
            actual_dict[key] = value


@shared_container_methods
@shared_set_methods
@functional_methods
@dataclass(slots=True)
class TypedSet(Generic[T]):
    item_type: type[T]
    values: set[T]

    def __init__(self: TypedSet[T], item_type: type[T], values: Iterable[T] | None = None) -> None:
        self.item_type = item_type
        self.values = set(_validate_values(values if values is not None else [], item_type))

    def add(self, value: T) -> None:
        self.values.add(_validate_value(value, self.item_type))

    def remove(self, value: T) -> None:
        self.values.remove(value)

    def discard(self, value: T) -> None:
        self.values.discard(value)


@shared_container_methods
@shared_set_methods
@functional_methods
@dataclass(frozen=True, slots=True)
class TypedFrozenSet(Generic[T]):
    item_type: type[T]
    values: set[T]

    def __init__(self, item_type: type[T], values: Iterable[T] | None = None):
        object.__setattr__(self, 'item_type', item_type)
        object.__setattr__(self, 'values', set(_validate_values(values if values is not None else [], item_type)))


@dataclass(frozen=True, slots=True)
class TypedOptional(Generic[T]):
    item_type: type[T]
    value: T | None

    def __init__(self: TypedOptional[T], item_type: type[T] | None = None, value: T | None = None) -> None:
        if value is not None and item_type is not None:
            object.__setattr__(self, 'item_type', item_type)
            object.__setattr__(self, 'value', _validate_value(value, item_type))
        elif value is not None and item_type is None:
            object.__setattr__(self, 'item_type', type(value))
            object.__setattr__(self, 'value', value)
        elif value is None and item_type is None:
            raise TypeError(f"You must provide either a type or a value.")
        else:
            object.__setattr__(self, 'item_type', item_type)
            object.__setattr__(self, 'value', None)

    @staticmethod
    def empty(item_type: type[T]) -> TypedOptional[T]:
        return TypedOptional(item_type, None)

    @staticmethod
    def of(value: T) -> TypedOptional[T]:
        if value is None:
            raise ValueError("Cannot create StaticOptional.of with None")
        return TypedOptional(type(value), value)

    @staticmethod
    def of_nullable(value: T | None, item_type: type[T]) -> TypedOptional[T]:
        if value is None:
            return TypedOptional.empty(item_type)
        return TypedOptional(item_type, value)

    def is_present(self: TypedOptional[T]) -> bool:
        return self.value is not None

    def is_empty(self: TypedOptional[T]) -> bool:
        return self.value is None

    def get(self: TypedOptional[T]) -> T:
        if self.is_empty():
            raise ValueError("No value present")
        return self.value

    def or_else(self: TypedOptional[T], fallback: T) -> T:
        return self.value or fallback

    def or_else_get(self: TypedOptional[T], supplier: Callable[[], T]) -> T:
        return self.value or supplier()

    def or_else_raise(self: TypedOptional[T], exception_supplier: Callable[[], Exception]) -> T:
        if self.is_present():
            return self.value
        raise exception_supplier()

    def if_present(self: TypedOptional[T], consumer: Callable[[T], None]) -> None:
        if self.is_present():
            consumer(self.value)

    def map(self: TypedOptional[T], f: Callable[[T], U]) -> TypedOptional[U]:
        if self.value is None:
            return TypedOptional.empty(object)
        result = f(self.value)
        if result is None:
            return TypedOptional.empty(object)
        return TypedOptional.of(result)

    def map_or_else(self, f: Callable[[T], U], fallback: U) -> U:
        if self.is_present():
            return f(self.value)
        else:
            return fallback

    def flatmap(self: TypedOptional[T], f: Callable[[T], TypedOptional[U]]) -> TypedOptional[U]:
        if self.is_empty():
            return TypedOptional.empty(self.item_type)
        result = f(self.value)
        if not isinstance(result, TypedOptional):
            raise TypeError("flatmap mapper must return StaticOptional")
        return result

    def filter(self: TypedOptional[T], predicate: Callable[[T], bool]) -> TypedOptional[T]:
        if self.is_empty() or not predicate(self.value):
            return TypedOptional.empty(self.item_type)
        return self

    def __bool__(self: TypedOptional[T]) -> bool:
        return bool(self.value) if self.is_present() else False

    def __repr__(self: TypedOptional[T]) -> str:
        return f"StaticOptional.of({self.value!r})" if self.is_present() else f"StaticOptional.empty({self.item_type.__name__})"