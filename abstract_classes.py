from __future__ import annotations

from functools import reduce
from typing import Iterable, Any, Callable, TypeVar, Generic, Mapping

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
A = TypeVar("A")
R = TypeVar("R")


def class_name(self: object) -> str:
    return type(self).__name__


def _forbid_instantiation(forbidden_type: type[T]) -> Callable[..., T]:
    def __new__(cls: type[T], *args, **kwargs) -> T:
        if cls is forbidden_type:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated directly.")
        return super(forbidden_type, cls).__new__(cls)
    return __new__


def _validate_value(item_type: type, value: object) -> object:
    """
    Checks if a single value is of a given type, or if it can be safely converted to that type. Valid conversions for
    now are int -> float, str -> (int, float) and Any -> str provided no error is raised.
    :param value: Value to check validity of.
    :param item_type: Type to check match for the value.
    :return: The value itself if it's of item_type, or its conversion to item_type if it can be safely converted to it.
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
    other_sets: list = []
    for iterable in others:
        other_sets.append(_validate_types(item_type, iterable, (Collection,), (Iterable,)))
    return other_sets


def _infer_type(values: Iterable[T]) -> type[T]:
    if values is None or not values:
        raise ValueError("Type can't be inferred from an empty iterable or None object.")

    inferred_type: type | None = None
    for value in values:
        if inferred_type is None:
            inferred_type = type(value)
        elif inferred_type != type(value):
            raise ValueError(f"There's a type mismatch: value {value} doesn't have type {inferred_type.__name__}, but {type(value).__name__}")
    return inferred_type


class Collection(Generic[T]):

    item_type: type[T]
    values: Any

    def __new__(cls, *args, **kwargs) -> Collection[T] | None:
        return _forbid_instantiation(Collection)(cls, *args, **kwargs)

    def __init__(
        self: Collection[T],
        item_type: type[T] | None = None,
        values: Iterable[T] | Collection[T] | None = None,
        forbidden_iterable_types: tuple[type, ...] = (),
        finisher: Callable[[Iterable[T]], Any] = lambda x : x
    ) -> None:
        obj_type: type[T] | None = None
        if item_type is None:
            # This raises a ValueError if the type can't be properly inferred.
            obj_type = _infer_type(values)

        if isinstance(values, forbidden_iterable_types):
            raise TypeError(f"Invalid type {type(values).__name__} for class {class_name(self)}.")
        object.__setattr__(self, 'item_type', item_type or obj_type)
        object.__setattr__(self, 'values', finisher(_validate_values(self.item_type, values)))

    def __len__(self: Collection[T]) -> int:
        return len(self.values)

    def __iter__(self: Collection[T]) -> Iterable[T]:
        return iter(self.values)

    def __contains__(self: Collection[T], item) -> bool:
        return item in self.values

    def __eq__(self: Collection[T], other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.item_type == other.item_type
            and self.values == other.values
        )

    def __repr__(self: Collection[T]) -> str:
        return f"{class_name(self)}<{self.item_type.__name__}>{self.values}"

    def __bool__(self: Collection[T]) -> bool:
        return bool(self.values)

    def copy(self: Collection[T]) -> Collection[T]:
        return self.__class__(self.item_type, self.values.copy() if hasattr(self.values, 'copy') else self.values)

    def to_list(self: Collection[T]) -> list[T]:
        return list(self.values)

    def to_tuple(self: Collection[T]) -> tuple[T]:
        return tuple(self.values)

    def to_set(self: Collection[T]) -> set[T]:
        return set(self.values)

    def to_frozen_set(self: Collection[T]) -> frozenset[T]:
        return frozenset(self.values)

    def count(self: Collection[T], value) -> int:
        try:
            return self.values.count(value)
        except AttributeError:
            return sum(1 for v in self.values if v == value)


    # Functional Methods:

    def map(self: Collection[T], f: Callable[[T], R]) -> Collection[R]:
        mapped = [f(value) for value in self.values]
        return self.__class__(type(mapped[0]) if mapped else object, mapped)

    def flatmap(self: Collection[T], f: Callable[[T], Iterable[R]]) -> Collection[R]:
        flattened = []
        for value in self.values:
            result = f(value)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        return self.__class__(type(flattened[0]) if flattened else object, flattened)

    def filter(self: Collection[T], predicate: Callable[[T], bool]) -> Collection[T]:
        return self.__class__(self.item_type, [value for value in self.values if predicate(value)])

    def all_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        return all(predicate(value) for value in self.values)

    def any_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        return any(predicate(value) for value in self.values)

    def none_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        return not any(predicate(value) for value in self.values)

    def reduce(self: Collection[T], f: Callable[[T, T], T], unit: T | None = None) -> T:
        if unit is not None:
            return reduce(f, self.values, unit)
        return reduce(f, self.values)

    def for_each(self: Collection[T], consumer: Callable[[T], None]) -> None:
        for value in self.values:
            consumer(value)

    def distinct(self: Collection[T], key: Callable[[T], K] = lambda x: x) -> Collection[T]:
        seen = set()
        result = []
        for value in self.values:
            key_of_value = key(value)
            if key_of_value not in seen:
                seen.add(key_of_value)
                result.append(value)
        return self.__class__(self.item_type, result)

    def max(self: Collection[T], *, default=None, key=None) -> T | None:
        if default is not None:
            return max(self.values, default=default, key=key)
        if not self.values:
            return None
        return max(self.values, key=key)

    def min(self: Collection[T], *, default=None, key=None) -> T | None:
        if default is not None:
            return min(self.values, default=default, key=key)
        if not self.values:
            return None
        return min(self.values, key=key)

    def collect(
        self: Collection[T],
        supplier: Callable[[], A],
        accumulator: Callable[[A, T], None],
        finisher: Callable[[A], R] = lambda x : x
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


class AbstractSequence(Collection[T]):

    def __new__(cls, *args, **kwargs) -> AbstractSequence[T] | None:
        return _forbid_instantiation(AbstractSequence)(cls, *args, **kwargs)

    def __getitem__(self: AbstractSequence[T], index: int | slice) -> T | AbstractSequence[T]:
        if isinstance(index, slice):
            return self.__class__(self.item_type, self.values[index])
        elif isinstance(index, int):
            return self.values[index]
        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __lt__(self: AbstractSequence[T], other) -> bool:
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) < tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __gt__(self: AbstractSequence[T], other) -> bool:
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) > tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __le__(self: AbstractSequence[T], other) -> bool:
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) <= tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __ge__(self: AbstractSequence[T], other) -> bool:
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) >= tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __add__(self: AbstractSequence[T], other) -> AbstractSequence[T]:
        return self.__class__(
            self.item_type,
            self.values + _validate_types(self.item_type, other, (AbstractSequence,), (list, tuple))
        )

    def __mul__(self: AbstractSequence[T], n: int) -> AbstractSequence[T]:
        if not isinstance(n, int):
            return NotImplemented
        return self.__class__(self.item_type, self.values * n)

    def __sub__(self: AbstractSequence[T], other) -> AbstractSequence[T]:
        other_values = _validate_types(self.item_type, other, (AbstractSequence,), (list, tuple))
        filtered_values = [value for value in self.values if value not in other_values]
        return self.__class__(self.item_type, filtered_values)

    def __reversed__(self: AbstractSequence[T]):
        return reversed(self.values)

    def index(self: AbstractSequence[T], value) -> int:
        return self.values.index(value)

    def sorted(self: AbstractSequence[T], key=None, reverse=False) -> AbstractSequence[T]:
        return self.__class__(self.item_type, sorted(self.values, key=key, reverse=reverse))


class AbstractMutableSequence(AbstractSequence[T]):

    def __new__(cls, *args, **kwargs) -> AbstractMutableSequence[T] | None:
        return _forbid_instantiation(AbstractMutableSequence)(cls, *args, **kwargs)

    def append(self: AbstractMutableSequence[T], value: T) -> None:
        self.values.append(_validate_value(self.item_type, value))

    def __setitem__(self: AbstractMutableSequence[T], index: int | slice, value: T | AbstractSequence[T] | list[T] | tuple[T]) -> None:
        if isinstance(index, slice):
            self.values[index] = _validate_types(self.item_type, value, (AbstractSequence,), (list, tuple))

        elif isinstance(index, int):
            self.values[index] = _validate_value(self.item_type, value)

        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __delitem__(self: AbstractMutableSequence[T], index: int | slice) -> None:
        del self.values[index]

    def sort(self: AbstractMutableSequence[T], key: Callable[[T], Any] | None = None, reverse: bool = False) -> None:
        self.values.sort(key=key, reverse=reverse)


class AbstractSet(Collection[T]):

    def __new__(cls, *args, **kwargs) -> AbstractSet[T] | None:
        return _forbid_instantiation(AbstractSet)(cls, *args, **kwargs)

    def union(self: AbstractSet[T], *others: Iterable[T]) -> AbstractSet[T]:
        return self.__class__(self.item_type, self.values.union(*_validate_multiple_sets(self.item_type, others)))

    def intersection(self: AbstractSet[T], *others: Iterable[T]) -> AbstractSet[T]:
        return self.__class__(self.item_type, self.values.intersection(*_validate_multiple_sets(self.item_type, others)))

    def difference(self: AbstractSet[T], *others: Iterable[T]) -> AbstractSet[T]:
        return self.__class__(self.item_type, self.values.difference(*_validate_multiple_sets(self.item_type, others)))

    def symmetric_difference(self: AbstractSet[T], *others: Iterable[T]) -> AbstractSet[T]:
        return self.__class__(self.item_type, self.values.symmetric_difference(*_validate_multiple_sets(self.item_type, others)))

    def is_subset(self: AbstractSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> bool:
        if isinstance(other, AbstractSet) and other.item_type != self.item_type:
            return False
        other_values = _validate_types(self.item_type, other, (AbstractSet,), (set, frozenset))
        return set.issubset(self.values, other_values)

    def is_superset(self: AbstractSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> bool:
        if isinstance(other, AbstractSet) and other.item_type != self.item_type:
            return False
        other_values = _validate_types(self.item_type, other, (AbstractSet,), (set, frozenset))
        return set.issuperset(self.values, other_values)

    def is_disjoint(self: AbstractSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> bool:
        if isinstance(other, AbstractSet) and other.item_type != self.item_type:
            return False
        other_values = _validate_types(self.item_type, other, (AbstractSet,), (set, frozenset))
        return set.isdisjoint(self.values, other_values)


class AbstractMutableSet(AbstractSet[T]):

    def __new__(cls, *args, **kwargs) -> AbstractMutableSet[T] | None:
        return _forbid_instantiation(AbstractMutableSet)(cls, *args, **kwargs)

    def add(self: AbstractMutableSet[T], value: T) -> None:
        self.values.add(_validate_value(self.item_type, value))

    def remove(self: AbstractMutableSet[T], value: T) -> None:
        self.values.remove(value)

    def discard(self: AbstractMutableSet[T], value: T) -> None:
        self.values.discard(value)

    def clear(self: AbstractMutableSet[T]) -> None:
        self.values.clear()

    def pop(self: AbstractMutableSet[T]) -> T:
        return self.values.pop()

    def update(self: AbstractMutableSet[T], *others: Iterable[T]) -> None:
        self.values.update(*_validate_multiple_sets(self.item_type, others))

    def difference_update(self: AbstractMutableSet[T], *others: Iterable[T]) -> None:
        self.values.difference_update(*_validate_multiple_sets(self.item_type, others))

    def intersection_update(self: AbstractMutableSet[T], *others: Iterable[T]) -> None:
        self.values.intersection_update(*_validate_multiple_sets(self.item_type, others))

    def symmetric_difference_update(self: AbstractMutableSet[T], *others: Iterable[T]) -> None:
        self.values.symmetric_difference_update(*_validate_multiple_sets(self.item_type, others))


class AbstractDict(Generic[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: dict

    def __new__(cls, *args, **kwargs) -> AbstractDict[K, V] | None:
        return _forbid_instantiation(AbstractDict)(cls, *args, **kwargs)

    def __init__(
        self: AbstractDict[K, V],
        key_type: type[K],
        value_type: type[V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        finisher: Callable[[dict[K, V]], Any] = lambda x : x
    ) -> None:
        object.__setattr__(self, "key_type", key_type)
        object.__setattr__(self, "value_type", value_type)

        if keys_values is None or not keys_values:
            object.__setattr__(self, "data", finisher({}))
            return

        if isinstance(keys_values, (dict, Mapping, AbstractDict)):
            keys = keys_values.keys()
            values = keys_values.values()
        elif isinstance(keys_values, Iterable):
            keys = [key for (key, _) in keys_values]
            values = [value for (_, value) in keys_values]
        else:
            raise TypeError(f"The values aren't a dict or Iterable.")

        if len(keys) != len(values):
            raise ValueError(f"The number of keys and values aren't equal.")

        actual_dict = {}

        for key, value in zip(_validate_values(key_type, keys), _validate_values(value_type, values)):
            actual_dict[key] = value

        object.__setattr__(self, "data", finisher(actual_dict))

    def __getitem__(self: AbstractDict[K, V], key: K) -> V:
        return self.data[key]

    def __iter__(self: AbstractDict[K, V]) -> Iterable[K]:
        return iter(self.data)

    def keys(self: AbstractDict[K, V]):
        return self.data.keys()

    def values(self: AbstractDict[K, V]):
        return self.data.values()

    def items(self: AbstractDict[K, V]):
        return self.data.items()

    def __len__(self: AbstractDict[K, V]):
        return len(self.data)

    def __contains__(self: AbstractDict[K, V], key: K) -> bool:
        return key in self.data

    def __eq__(self: AbstractDict[K, V], other) -> bool:
        if type(self) != type(other):
            return NotImplemented
        return (
            self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def __repr__(self: AbstractDict[K, V]) -> str:
        return f"{class_name(self)}<{self.key_type.__name__}, {self.value_type.__name__}>{self.data}"

    def copy(self: AbstractDict[K, V]) -> AbstractDict[K, V]:
        return self.__class__(self.key_type, self.value_type, self.data.copy())

    def get(self: AbstractDict[K, V], key: K, fallback: V | None = None) -> V | None:
        return self.data.get(key, fallback)

    def map_values(self: AbstractDict[K, V], f: Callable[[V], R]) -> AbstractDict[K, R]:
        new_data = {key : f(value) for key, value in self.data.items()}
        return self.__class__(
            self.key_type,
            type(next(iter(new_data.values()), object)),
            new_data
        )

    def filter_keys(self: AbstractDict[K, V], predicate: Callable[[K], bool]) -> AbstractDict[K, V]:
        return self.__class__(
            self.key_type,
            self.value_type,
            {key: value for key, value in self.data.items() if predicate(key)}
        )

    def filter_values(self: AbstractDict[K, V], predicate: Callable[[V], bool]) -> AbstractDict[K, V]:
        return self.__class__(
            self.key_type,
            self.value_type,
            {key: value for key, value in self.data.items() if predicate(value)}
        )

    def filter_items(self: AbstractDict[K, V], predicate: Callable[[K, V], bool]) -> AbstractDict[K, V]:
        return self.__class__(
            self.key_type,
            self.value_type,
            {key: value for key, value in self.data.items() if predicate(key, value)}
        )

    def subdict(self: AbstractDict[K, V], start: K, end: K) -> AbstractDict[K, V]:
        try:
            if start > end:
                raise ValueError()
        except TypeError:
            raise TypeError("Keys must support ordering for subdict slicing.")
        except ValueError:
            raise ValueError("Start must be lower than end.")

        return self.__class__(
            self.key_type,
            self.value_type,
            {key: value for key, value in self.data.items() if start <= key <= end}
        )


class AbstractMutableDict(AbstractDict[K, V]):

    def __new__(cls, *args, **kwargs) -> AbstractMutableDict[K, V] | None:
        return _forbid_instantiation(AbstractMutableDict)(cls, *args, **kwargs)

    def __setitem__(self: AbstractMutableDict[K, V], key: K, value: V) -> None:
        self.data[_validate_value(self.key_type, key)] = _validate_value(self.value_type, value)

    def __delitem__(self: AbstractMutableDict[K, V], key: K) -> None:
        del self.data[key]

    def clear(self: AbstractMutableDict[K, V]) -> None:
        self.data.clear()

    def update(self: AbstractMutableDict[K, V], other: dict[K, V] | Mapping[K, V] | AbstractDict[K, V]) -> None:
        if isinstance(other, AbstractDict):
            if not issubclass(other.key_type, self.key_type):
                raise TypeError(f"Cannot update with StaticDict of keys {other.key_type.__name__}")
            if not issubclass(other.value_type, self.value_type):
                raise TypeError(f"Cannot update with StaticDict of values {other.value_type.__name__}")
            other_items = other.data.items()

        elif isinstance(other, (dict, Mapping)):
            validated_keys = _validate_values(self.key_type, other.keys())
            validated_values = _validate_values(self.value_type, other.values())
            other_items = dict(zip(validated_keys, validated_values)).items()

        else:
            raise TypeError("'others' argument must be a dict or MutableDict")

        for key, value in other_items:
            self[key] = value

    def pop(self: AbstractMutableDict[K, V], key: K, default: V | None = None) -> V:
        if default is not None:
            return self.data.pop(_validate_value(self.key_type, key), default)
        return self.data.pop(_validate_value(self.key_type, key))

    def popitem(self: AbstractMutableDict[K, V]) -> tuple[K, V]:
        return self.data.popitem()

    def setdefault(self: AbstractMutableDict[K, V], key: K, default: V) -> V:
        key = _validate_value(self.key_type, key)
        default = _validate_value(self.value_type, default)
        return self.data.setdefault(key, default)
