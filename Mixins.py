from __future__ import annotations

from functools import reduce
from typing import Iterable, Any, Callable, TypeVar, Protocol, runtime_checkable

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
A = TypeVar("A")
R = TypeVar("R")


def get_class_name(self: object) -> str:
    return self.__class__.__name__


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


def _validate_values(actual_values: Iterable, item_type: type) -> list:
    """
    Checks if all elements of the given Iterable are of the given type or a subclass thereof. If not, raises a TypeError.
    :param actual_values: Iterable of values of possibly different types.
    :param item_type: Type to check for.
    :return: A list of values validated as per the _validate_value function, coercing certain types like int to float
    and str to int or float if possible.
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


@runtime_checkable
class TypedCollection(Protocol[T]):
    item_type: type[T]
    values: Any

    def __init__(self, item_type, values): ...


@runtime_checkable
class TypedDictionary(Protocol[K, V]):
    key_type: type[K]
    value_type: type[V]
    data: dict

    def __init__(self, key_type, value_type, keys_values = None): ...


class FunctionalMethods(TypedCollection[T]):
    """
    Mixin class that defines common functional methods for classes to inherit. The class should have a values attribute,
    usually a list, tuple or set, and an item_type describing the type of the values. Currently, the functional methods
    implemented are:
    <ul>
        <li>map</li>
        <li>flatmap</li>
        <li>filter</li>
        <li>all_match</li>
        <li>any_match</li>
        <li>none_match</li>
        <li>reduce</li>
        <li>for_each</li>
        <li>distinct</li>
    </ul>
    """

    def map(self: TypedCollection[T], f: Callable[[T], R]) -> TypedCollection[R]:
        mapped = [f(value) for value in self.values]
        item_type = type(mapped[0]) if mapped else object
        return self.__class__(item_type, mapped)

    def flatmap(self: TypedCollection[T], f: Callable[[T], Iterable[R]]) -> TypedCollection[R]:
        flattened = []
        for value in self.values:
            result = f(value)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        return self.__class__(type(flattened[0]) if flattened else object, flattened)

    def filter(self: TypedCollection[T], predicate: Callable[[T], bool]) -> TypedCollection[T]:
        return self.__class__(self.item_type, [value for value in self.values if predicate(value)])

    def all_match(self: TypedCollection[T], predicate: Callable[[T], bool]) -> bool:
        return all(predicate(value) for value in self.values)

    def any_match(self: TypedCollection[T], predicate: Callable[[T], bool]) -> bool:
        return any(predicate(value) for value in self.values)

    def none_match(self: TypedCollection[T], predicate: Callable[[T], bool]) -> bool:
        return not any(predicate(value) for value in self.values)

    def reduce(self: TypedCollection[T], f: Callable[[T, T], T], initializer: T | None = None) -> T:
        if initializer is not None:
            return reduce(f, self.values, initializer)
        return reduce(f, self.values)

    def for_each(self: TypedCollection[T], consumer: Callable[[T], None]) -> None:
        for value in self.values:
            consumer(value)

    def distinct(self: TypedCollection[T], key: Callable[[T], K] | None = None) -> TypedCollection[T]:
        seen = set()
        result = []
        for value in self.values:
            key_of_value = value if key is None else key(value)
            if key_of_value not in seen:
                seen.add(key_of_value)
                result.append(value)
        return self.__class__(self.item_type, result)

    def max(self: TypedCollection[T], *, default=None, key=None) -> T | None:
        if default is not None:
            return max(self.values, default=default, key=key)
        if not self.values:
            return None
        return max(self.values, key=key)

    def min(self: TypedCollection[T], *, default=None, key=None) -> T | None:
        if default is not None:
            return min(self.values, default=default, key=key)
        if not self.values:
            return None
        return min(self.values, key=key)

    def collect(
        self: TypedCollection[T],
        supplier: Callable[[], A],
        accumulator: Callable[[A, T], None],
        finisher: Callable[[A], R] = lambda x: x
    ) -> R:
        """
        Generalized collector, replicating Java's Stream API .collect method.
        :param supplier: A function that provides the initial container.
        :param accumulator: A function that adds one item into the container.
        :param finisher: Optional function to finalize the container into another form.
        :return: The collected result.
        """
        acc = supplier()
        for item in self.values:
            accumulator(acc, item)
        return finisher(acc)


class Collection(TypedCollection[T]):

    def __len__(self: TypedCollection[T]) -> int:
        return len(self.values)

    def __iter__(self: TypedCollection[T]) -> Iterable[T]:
        return iter(self.values)

    def __contains__(self: TypedCollection[T], item) -> bool:
        return item in self.values

    def __eq__(self: TypedCollection[T], other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.item_type == other.item_type
            and self.values == other.values
        )

    def __repr__(self: TypedCollection[T]) -> str:
        return f"{get_class_name(self)}<{self.item_type.__name__}>{self.values}"

    def __bool__(self: TypedCollection[T]) -> bool:
        return bool(self.values)

    def copy(self: TypedCollection[T]) -> TypedCollection[T]:
        return self.__class__(self.item_type, self.values.copy() if hasattr(self.values, 'copy') else self.values)

    def to_list(self: TypedCollection[T]) -> list[T]:
        return list(self.values)

    def to_tuple(self: TypedCollection[T]) -> tuple[T]:
        return tuple(self.values)

    def to_set(self: TypedCollection[T]) -> set[T]:
        return set(self.values)

    def to_frozen_set(self: TypedCollection[T]) -> frozenset[T]:
        return frozenset(self.values)

    def count(self: TypedCollection[T], value) -> int:
        try:
            return self.values.count(value)
        except AttributeError:
            return sum(1 for v in self.values if v == value)


class Sequence(Collection[T]):

    def __getitem__(self: Sequence[T], index: int | slice) -> T | Sequence[T]:
        if isinstance(index, slice):
            return self.__class__(self.item_type, self.values[index])
        elif isinstance(index, int):
            return self.values[index]
        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __lt__(self: Sequence[T], other) -> bool:
        if isinstance(other, (Sequence, list, tuple)):
            return tuple(self.values) < tuple(other.values if isinstance(other, TypedCollection) else other)
        return NotImplemented

    def __gt__(self: Sequence[T], other) -> bool:
        if isinstance(other, (Sequence, list, tuple)):
            return tuple(self.values) > tuple(other.values if isinstance(other, TypedCollection) else other)
        return NotImplemented

    def __le__(self: Sequence[T], other) -> bool:
        if isinstance(other, (Sequence, list, tuple)):
            return tuple(self.values) <= tuple(other.values if isinstance(other, TypedCollection) else other)
        return NotImplemented

    def __ge__(self: Sequence[T], other) -> bool:
        if isinstance(other, (Sequence, list, tuple)):
            return tuple(self.values) >= tuple(other.values if isinstance(other, Sequence) else other)
        return NotImplemented

    def __add__(self: Sequence[T], other) -> Sequence[T]:
        return self.__class__(
            self.item_type,
            self.values + _validate_types(self, other, (Sequence), (list, tuple))
        )

    def __mul__(self: Sequence[T], n) -> Sequence[T]:
        if not isinstance(n, int):
            return NotImplemented
        return self.__class__(self.item_type, self.values * n)

    def __sub__(self: Sequence[T], other) -> Sequence[T]:
        other_values = _validate_types(self, other, (Sequence), (list, tuple))
        filtered_values = [value for value in self.values if value not in other_values]
        return self.__class__(self.item_type, filtered_values)

    def __reversed__(self: Sequence[T]):
        return reversed(self.values)

    def index(self: Sequence[T], value) -> int:
        return self.values.index(value)

    def sorted(self: Sequence[T], key=None, reverse=False) -> Sequence[T]:
        return self.__class__(self.item_type, sorted(self.values, key=key, reverse=reverse))


class Set(Collection[T]):

    def union(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> Set[T]:
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return self.__class__(self.item_type, set.union(self.values, other_values))

    def intersection(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> Set[T]:
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return self.__class__(self.item_type, set.intersection(self.values, other_values))

    def difference(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> Set[T]:
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return self.__class__(self.item_type, set.difference(self.values, other_values))

    def symmetric_difference(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> Set[T]:
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return self.__class__(self.item_type, set.symmetric_difference(self.values, other_values))

    def is_subset(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> bool:
        if isinstance(other, Set) and other.item_type != self.item_type:
            return False
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return set.issubset(self.values, other_values)

    def is_superset(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> bool:
        if isinstance(other, Set) and other.item_type != self.item_type:
            return False
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return set.issuperset(self.values, other_values)

    def is_disjoint(self: Set[T], other: Set[T] | set[T] | frozenset[T]) -> bool:
        if isinstance(other, Set) and other.item_type != self.item_type:
            return False
        other_values = _validate_types(self, other, (Set), (set, frozenset))
        return set.isdisjoint(self.values, other_values)


class Dictionary(TypedDictionary[K, V]):

    def __getitem__(self: Dictionary[K, V], key: K) -> V:
        return self.data[key]

    def __iter__(self: Dictionary[K, V]) -> Iterable[K]:
        return iter(self.data)

    def keys(self: Dictionary[K, V]):
        return self.data.keys()

    def values(self: Dictionary[K, V]):
        return self.data.values()

    def items(self: Dictionary[K, V]):
        return self.data.items()

    def __len__(self: Dictionary[K, V]):
        return len(self.data)

    def __contains__(self: Dictionary[K, V], key: K) -> bool:
        return key in self.data

    def __eq__(self: Dictionary[K, V], other) -> bool:
        if type(self) != type(other):
            return NotImplemented
        return (
            self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def __repr__(self: Dictionary[K, V]) -> str:
        return f"{get_class_name(self)}<{self.key_type.__name__}, {self.value_type.__name__}>{self.values}"

    def copy(self: Dictionary[K, V]) -> Dictionary[K, V]:
        return self.__class__(self.key_type, self.value_type, self.data.copy())

    def get(self: Dictionary[K, V], key: K, fallback: V | None = None) -> V | None:
        return self.data.get(key, fallback)

    def map_values(self: Dictionary[K, V], f: Callable[[V], R]) -> Dictionary[K, R]:
        new_data = {key : f(value) for key, value in self.data.items()}
        new_value_type = type(next(iter(new_data.values()), object))
        return self.__class__(self.key_type, new_value_type, new_data)

    def filter_items(self: Dictionary[K, V], predicate: Callable[[K, V], bool]) -> Dictionary[K, V]:
        filtered = {key : value for key, value in self.data.items() if predicate(key, value)}
        return self.__class__(self.key_type, self.value_type, filtered)

    def subdict(self: Dictionary[K, V], start: K, end: K) -> Dictionary[K, V]:
        try:
            if start > end:
                raise TypeError("Start must be lower than end.")
        except TypeError:
            raise TypeError("Keys must support ordering for subdict slicing.")

        sliced_data = {key : value for key, value in self.data.data() if start <= key <= end}
        return self.__class__(self.key_type, self.value_type, sliced_data)
