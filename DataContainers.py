from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar, Generic, Callable, Any, Iterable

import frozendict

from Mixins import _validate_value, _validate_values, _validate_types, FunctionalMixin, ContainerMixin, SequenceMixin, \
    SetMixin, DictMixin

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")


@dataclass(slots=True, repr=False)
class TypedList(FunctionalMixin, ContainerMixin, SequenceMixin, Generic[T]):

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


@dataclass(frozen=True, slots=True, repr=False)
class TypedTuple(FunctionalMixin, ContainerMixin, SequenceMixin, Generic[T]):

    item_type: type[T]
    values: tuple[T, ...] = field(default_factory=tuple)

    def __init__(self, item_type: type[T], values: Iterable[T] = ()):
        if isinstance(values, (set, frozenset)):
            raise TypeError("StaticTuple does not accept set or frozenset because their order is not guaranteed")
        object.__setattr__(self, 'item_type', item_type)
        object.__setattr__(self, 'values', _validate_values(values, item_type))


@dataclass(slots=True)
class TypedDict(DictMixin, Generic[K, V]):

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

        elif isinstance(other, (dict, frozendict)):
            validated_keys = _validate_values(other.keys(), self.key_type)
            validated_values = _validate_values(other.values(), self.value_type)
            other_items = dict(zip(validated_keys, validated_values)).items()

        else:
            raise TypeError("'other' argument must be dict or StaticDict")

        for key, value in other_items:
            self[key] = value

    def map_values(self: TypedDict[K, V], f: Callable[[V], U]) -> TypedDict[K, U]:
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


@dataclass(frozen=True, slots=True)
class TypedFrozenDict(DictMixin, Generic[K, V]):
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


@dataclass(slots=True, repr=False)
class TypedSet(FunctionalMixin, ContainerMixin, SetMixin, Generic[T]):
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


@dataclass(frozen=True, slots=True, repr=False)
class TypedFrozenSet(FunctionalMixin, ContainerMixin, SetMixin, Generic[T]):
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