from __future__ import annotations

from functools import reduce
from typing import Iterable, Any, Callable, Mapping, TYPE_CHECKING, TypeVar
from collections import defaultdict

from GenericBase import GenericBase, class_name

if TYPE_CHECKING:
    from type_validation import (
        _validate_or_coerce_value,
        _validate_or_coerce_iterable,
        _validate_collection_type_and_get_values,
        _validate_or_coerce_iterable_of_iterables,
        _infer_type_contained_in_iterable
    )


def _forbid_instantiation[T](forbidden_type: type[T]) -> Callable[..., T]:
    """
    Generates a __new__ method that raises a TypeError if the class that is trying to be instantiated is of the
    forbidden type.
    :param forbidden_type: Type for the instantiation to be forbidden.
    :return: A __new__ method that, no matter the arguments received, raises a TypeError if the class that tried
    to call iterable was of the forbidden type.
    """
    def __new__(cls: type[T], *args, **kwargs) -> T:
        if cls is forbidden_type:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated directly.")
        return super(forbidden_type, cls).__new__(cls)
    return __new__


class Collection[T](GenericBase[T]):

    item_type: type[T]
    values: Any

    def __new__(cls, *args, **kwargs) -> Collection[T] | None:
        return _forbid_instantiation(Collection)(cls, *args, **kwargs)

    def __init__(
        self: Collection[T],
        *values: Iterable[T] | Collection[T] | T,
        _coerce: bool = False,
        _forbidden_iterable_types: tuple[type, ...] = (),
        _finisher: Callable[[Iterable[T]], Any] = lambda x : x,
        _skip_validation: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_iterable

        generic_item_type = type(self)._inferred_item_type()

        if generic_item_type is None:
            raise TypeError(f"{type(self).__name__} must be instantiated with a concrete type, e.g., MutableList[int](...) or via .of().")

        if isinstance(generic_item_type, TypeVar):
            raise TypeError(f"{type(self).__name__} was instantiated without a concrete type, somehow {generic_item_type} was a TypeVar.")

        if len(values) == 1 and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            values = values[0]

        if isinstance(values, _forbidden_iterable_types):
            raise TypeError(f"Invalid type {type(values).__name__} for class {type(self).__name__}.")

        object.__setattr__(self, 'item_type', generic_item_type)

        final_values = values if _skip_validation else _validate_or_coerce_iterable(values, self.item_type, _coerce=_coerce)

        object.__setattr__(self, 'values', _finisher(final_values))

    @classmethod
    def _inferred_item_type(cls: Collection[T]) -> type[T] | None:
        try:
            return cls._args[0]
        except (AttributeError, IndexError, TypeError, KeyError):
            return None

    @classmethod
    def of(cls: type[Collection[T]], *values: T):
        if not values:
            raise ValueError(f"Can't create a {cls.__name__} object from empty iterable.")

        if len(values) == 1 and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            values = tuple(values[0])

        from type_validation import _infer_type_contained_in_iterable
        return cls[_infer_type_contained_in_iterable(values)](values)

    @classmethod
    def empty[R](cls: type[Collection[R]], item_type: type[R]) -> Collection[R]:
        if item_type is None:
            raise ValueError(f"Trying to call {cls.__name__}.empty with a None type.")
        return cls[item_type]()

    def __len__(self: Collection[T]) -> int:
        return len(self.values)

    def __iter__(self: Collection[T]) -> Iterable[T]:
        return iter(self.values)

    def __contains__(self: Collection[T], item: object) -> bool:
        return item in self.values

    def __eq__(self: Collection[T], other: Any) -> bool:
        return (
            issubclass(type(self), Collection)
            and issubclass(type(other), Collection)
            and self.item_type == other.item_type
            and self.values == other.values
        )

    def __repr__(self: Collection[T]) -> str:
        cls = type(self)
        return f"{class_name(cls)}{self.values}"

    def __bool__(self: Collection[T]) -> bool:
        return bool(self.values)

    # TODO tests
    def copy(self: Collection[T], deep: bool = False) -> Collection[T]:
        from copy import deepcopy
        values = deepcopy(self.values) if deep else (self.values.copy() if hasattr(self.values, 'copy') else self.values)
        return type(self)[self.item_type](values, _skip_validation=True)

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

    # TODO tests
    def map[R](
        self: Collection[T],
        f: Callable[[T], R],
        result_type: type[R] | None = None,
        coerce: bool = False
    ) -> Collection[R]:
        mapped_values = [f(value) for value in self.values]
        return type(self)[result_type](mapped_values, _coerce=coerce) if result_type is not None else type(self).of(mapped_values)

    # TODO tests
    def flatmap[R](
        self: Collection[T],
        f: Callable[[T], Iterable[R]],
        result_type: type[R] | None = None,
        coerce: bool = False
    ) -> Collection[R]:
        flattened = []
        for value in self.values:
            result = f(value)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        return type(self)[result_type](flattened, _coerce=coerce) if result_type is not None else type(self).of(flattened)

    def filter(self: Collection[T], predicate: Callable[[T], bool]) -> Collection[T]:
        return type(self)([value for value in self.values if predicate(value)], _skip_validation=True)

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

    def peek(self: Collection[T], consumer: Callable[[T], None]) -> Collection[T]:
        for item in self.values:
            consumer(item)
        return self

    def distinct[K](self: Collection[T], key: Callable[[T], K] = lambda x: x) -> Collection[T]:
        seen = set()
        result = []
        for value in self.values:
            key_of_value = key(value)
            if key_of_value not in seen:
                seen.add(key_of_value)
                result.append(value)
        return type(self)(result, _skip_validation=True)

    def max(self: Collection[T], *, default: T = None, key: Callable[[T], Any] = None) -> T | None:
        if default is not None:
            return max(self.values, default=default, key=key)
        if not self.values:
            return None
        return max(self.values, key=key)

    def min(self: Collection[T], *, default: T = None, key: Callable[[T], Any] = None) -> T | None:
        if default is not None:
            return min(self.values, default=default, key=key)
        if not self.values:
            return None
        return min(self.values, key=key)

    # TODO tests
    def group_by[K](
        self: Collection[T],
        key: Callable[[T], K]
    ) -> dict[K, Collection[T]]:
        groups: dict[K, list[T]] = defaultdict(list)
        for item in self.values:
            groups[key(item)].append(item)
        return {
            key : type(self)[self.item_type](group, _skip_validation=True)
            for key, group in groups.items()
        }

    # TODO tests
    def partition_by(
        self: Collection[T],
        predicate: Callable[[T], bool]
    ) -> dict[bool, Collection[T]]:
        true_part, false_part = [], []
        for item in self.values:
            (true_part if predicate(item) else false_part).append(item)
        return {
            True: type(self)(true_part, _skip_validation=True),
            False: type(self)(false_part, _skip_validation=True)
        }

    def collect[A, R](
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


class AbstractSequence[T](Collection[T]):

    def __new__(cls, *args, **kwargs) -> AbstractSequence[T] | None:
        return _forbid_instantiation(AbstractSequence)(cls, *args, **kwargs)

    def __getitem__(self: AbstractSequence[T], index: int | slice) -> T | AbstractSequence[T]:
        if isinstance(index, slice):
            return type(self)[self.item_type](self.values[index])
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

    def __add__(
        self: AbstractSequence[T],
        other: AbstractSequence[T] | list[T] | tuple[T]
    ) -> AbstractSequence[T]:
        from type_validation import _validate_collection_type_and_get_values
        return type(self)(self.values + _validate_collection_type_and_get_values(other, self.item_type))

    def __mul__(
        self: AbstractSequence[T],
        n: int
    ) -> AbstractSequence[T]:
        if not isinstance(n, int):
            return NotImplemented
        return type(self)(self.values * n, _skip_validation=True)

    def __sub__(self: AbstractSequence[T], other) -> AbstractSequence[T]:
        from type_validation import _validate_collection_type_and_get_values
        other_values = _validate_collection_type_and_get_values(other, self.item_type)
        filtered_values = [value for value in self.values if value not in other_values]
        return type(self)(filtered_values, _skip_validation=True)

    def __reversed__(self: AbstractSequence[T]):
        return reversed(self.values)

    def index(self: AbstractSequence[T], value) -> int:
        return self.values.index(value)

    def sorted(self: AbstractSequence[T], key=None, reverse=False) -> AbstractSequence[T]:
        return type(self)(sorted(self.values, key=key, reverse=reverse), _skip_validation=True)


class AbstractMutableSequence[T](AbstractSequence[T]):

    def __new__(cls, *args, **kwargs) -> AbstractMutableSequence[T] | None:
        return _forbid_instantiation(AbstractMutableSequence)(cls, *args, **kwargs)

    def append(
        self: AbstractMutableSequence[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value
        self.values.append(_validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def __setitem__(
        self: AbstractMutableSequence[T],
        index: int | slice,
        value: T | AbstractSequence[T] | list[T] | tuple[T],
        *,
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_collection_type_and_get_values, _validate_or_coerce_value

        if isinstance(index, slice):
            self.values[index] = _validate_collection_type_and_get_values(value, self.item_type)

        elif isinstance(index, int):
            self.values[index] = _validate_or_coerce_value(value, self.item_type, _coerce=_coerce)

        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __delitem__(self: AbstractMutableSequence[T], index: int | slice) -> None:
        del self.values[index]

    def sort(self: AbstractMutableSequence[T], key: Callable[[T], Any] | None = None, reverse: bool = False) -> None:
        self.values.sort(key=key, reverse=reverse)


class AbstractSet[T](Collection[T]):

    def __new__(cls, *args, **kwargs) -> AbstractSet[T] | None:
        return _forbid_instantiation(AbstractSet)(cls, *args, **kwargs)

    def union(
        self: AbstractSet[T],
        *others: Iterable[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.union(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)))

    def intersection(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.intersection(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)))

    def difference(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.difference(*_validate_or_coerce_iterable_of_iterables(others, self.item_type,_coerce=_coerce)))

    def symmetric_difference(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        new_values = self.values
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            new_values = new_values.symmetric_difference(validated_set)
        return type(self)(new_values)

    def is_subset(
        self: AbstractSet[T],
        other: AbstractSet[T] | set[T] | frozenset[T],
        *,
        _coerce: bool = False
    ) -> bool:
        from type_validation import _validate_collection_type_and_get_values
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.issubset(_validate_collection_type_and_get_values(other, self.item_type, _coerce=_coerce))

    def is_superset(
        self: AbstractSet[T],
        other: AbstractSet[T] | set[T] | frozenset[T],
        *,
        _coerce: bool = False
    ) -> bool:
        from type_validation import _validate_collection_type_and_get_values
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.issuperset(_validate_collection_type_and_get_values(other, self.item_type, _coerce=_coerce))

    def is_disjoint(
        self: AbstractSet[T],
        other: AbstractSet[T] | set[T] | frozenset[T],
        *,
        _coerce: bool = False
    ) -> bool:
        from type_validation import _validate_collection_type_and_get_values
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.isdisjoint(_validate_collection_type_and_get_values(other, self.item_type, _coerce=_coerce))


class AbstractMutableSet[T](AbstractSet[T]):

    def __new__(cls, *args, **kwargs) -> AbstractMutableSet[T] | None:
        return _forbid_instantiation(AbstractMutableSet)(cls, *args, **kwargs)

    def add(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value
        self.values.add(_validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def remove(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value
        if _coerce:
            try:
                self.values.remove(_validate_or_coerce_value(value, self.item_type))
                return
            except (TypeError, ValueError):
                pass
        self.values.remove(value)

    def discard(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value
        if _coerce:
            try:
                self.values.discard(_validate_or_coerce_value(value, self.item_type))
                return
            except (TypeError, ValueError):
                pass
        self.values.discard(value)

    def clear(self: AbstractMutableSet[T]) -> None:
        self.values.clear()

    def pop(self: AbstractMutableSet[T]) -> T:
        return self.values.pop()

    def update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def difference_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.difference_update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def intersection_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.intersection_update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def symmetric_difference_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_iterable_of_iterables
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            self.values.symmetric_difference_update(validated_set)


class AbstractDict[K, V](GenericBase[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __new__(cls, *args, **kwargs) -> AbstractDict[K, V] | None:
        return _forbid_instantiation(AbstractDict)(cls, *args, **kwargs)

    def __init__(
        self: AbstractDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None,
        _coerce_keys: bool = False,
        _coerce_values: bool = False,
        _finisher: Callable[[dict[K, V]], Any] = lambda x : x,
        _skip_validation: bool = False
    ) -> None:
        from type_validation import (
            _validate_or_coerce_iterable,
            _split_keys_values,
            _validate_duplicates_and_hash
        )

        key_type, value_type = type(self)._inferred_key_value_types()

        if key_type is None or value_type is None:
            raise TypeError(f"Not all generic types were provided. Key: {key_type} | Value: {value_type}")

        if isinstance(key_type, TypeVar) or isinstance(value_type, TypeVar):
            raise TypeError(f"Generic types must be fully specified for {type(self).__name__}. Use {type(self).__name__}.of(...) to infer types from iterable.")

        object.__setattr__(self, "key_type", key_type)
        object.__setattr__(self, "value_type", value_type)

        if keys_values is None and (_keys is None or _values is None):
            object.__setattr__(self, "data", _finisher({}))
            return

        if _keys is not None and _values is not None:
            keys = _keys
            values = _values
            if len(list(keys)) != len(list(values)):
                raise ValueError("Keys and iterable must be of the same length.")
            keys_from_iterable = True
        else:
            keys, values, keys_from_iterable = _split_keys_values(keys_values)

        actual_keys = keys if _skip_validation else _validate_or_coerce_iterable(keys, self.key_type, _coerce=_coerce_keys)
        actual_values = values if _skip_validation else _validate_or_coerce_iterable(values, self.value_type, _coerce=_coerce_values)

        if keys_from_iterable:
            _validate_duplicates_and_hash(actual_keys)

        object.__setattr__(self, "data", _finisher(dict(zip(actual_keys, actual_values))))

    @classmethod
    def _inferred_key_value_types(cls: AbstractDict[K, V]) -> tuple[type[K] | None, type[V] | None]:
        try:
            key_type = cls._args[0]
            value_type = cls._args[1]
        except (TypeError, ValueError, IndexError, KeyError):
            key_type = None
            value_type = None
        return key_type, value_type

    @classmethod
    def of(cls: type[AbstractDict[K, V]], keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]):
        if keys_values is None or not keys_values:
            raise ValueError(f"Can't create a {cls.__name__} object from empty iterable.")
        from type_validation import _infer_type_contained_in_iterable, _split_keys_values
        keys, values, _ = _split_keys_values(keys_values)
        key_type = _infer_type_contained_in_iterable(keys)
        value_type = _infer_type_contained_in_iterable(values)
        return cls[key_type, value_type](_keys=keys, _values=values)

    @classmethod
    def of_keys_values(cls: type[AbstractDict[K, V]], keys: Iterable[K], values: Iterable[V]):
        keys = list(keys)
        values = list(values)

        if len(keys) != len(values):
            raise ValueError("Keys and iterable must be of the same length when using .of_keys_values")

        from type_validation import _infer_type_contained_in_iterable, _validate_duplicates_and_hash
        key_type = _infer_type_contained_in_iterable(keys)
        value_type = _infer_type_contained_in_iterable(values)
        return cls[key_type, value_type](_keys=keys, _values=values)

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

    def __len__(self: AbstractDict[K, V]) -> int:
        return len(self.data)

    def __contains__(self: AbstractDict[K, V], key: object) -> bool:
        return key in self.data

    def __eq__(self: AbstractDict[K, V], other: Any) -> bool:
        return (
            issubclass(type(self), AbstractDict)
            and issubclass(type(other), AbstractDict)
            and self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def __repr__(self: AbstractDict[K, V]) -> str:
        return f"{class_name(type(self))}{dict(self.data)}"

    def copy(self: AbstractDict[K, V]) -> AbstractDict[K, V]:
        return type(self)(self.data.copy())

    def get(
        self: AbstractDict[K, V],
        key: K,
        fallback: V | None = None,
        *,
        _coerce_keys: bool = False,
        _coerce_values: bool = False
    ) -> V | None:
        from type_validation import _validate_or_coerce_value
        if _coerce_keys:
            try:
                key = _validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys)
            except TypeError:
                pass
        return self.data.get(
            key,
            _validate_or_coerce_value(fallback, self.value_type, _coerce=_coerce_values) if fallback is not None else None
        )

    def map_values[R](
        self: AbstractDict[K, V],
        f: Callable[[V], R],
        result_type: type[R] | None = None,
        *,
        _coerce_values: bool = False
    ) -> AbstractDict[K, R]:
        from type_validation import _infer_type_contained_in_iterable
        new_data = {key : f(value) for key, value in self.data.items()}
        if result_type is not None:
            return type(self)[self.key_type, result_type](new_data, _coerce_values=_coerce_values)
        else:
            inferred_return_type = _infer_type_contained_in_iterable(new_data.values())
            return type(self)[self.key_type, inferred_return_type](new_data, _skip_validation=True)

    def filter_keys(self: AbstractDict[K, V], predicate: Callable[[K], bool]) -> AbstractDict[K, V]:
        return type(self)({key : value for key, value in self.data.items() if predicate(key)})

    def filter_values(self: AbstractDict[K, V], predicate: Callable[[V], bool]) -> AbstractDict[K, V]:
        return type(self)({key : value for key, value in self.data.items() if predicate(value)})

    def filter_items(self: AbstractDict[K, V], predicate: Callable[[K, V], bool]) -> AbstractDict[K, V]:
        return type(self)({key : value for key, value in self.data.items() if predicate(key, value)})

    def subdict(self: AbstractDict[K, V], start: K, end: K) -> AbstractDict[K, V]:
        try:
            if start >= end:
                raise ValueError()
        except TypeError:
            raise TypeError("Keys must support ordering for subdict slicing.")
        except ValueError:
            raise ValueError("Start must be lower than end.")
        return self.filter_keys(lambda key : start <= key <= end)


class AbstractMutableDict[K, V](AbstractDict[K, V]):

    def __new__(cls, *args, **kwargs) -> AbstractMutableDict[K, V] | None:
        return _forbid_instantiation(AbstractMutableDict)(cls, *args, **kwargs)

    def __setitem__(self: AbstractMutableDict[K, V], key: K, value: V) -> None:
        from type_validation import _validate_or_coerce_value
        self.data[_validate_or_coerce_value(key, self.key_type)] = _validate_or_coerce_value(value, self.value_type)

    def __delitem__(self: AbstractMutableDict[K, V], key: K) -> None:
        del self.data[key]

    def clear(self: AbstractMutableDict[K, V]) -> None:
        self.data.clear()

    def update(
        self: AbstractMutableDict[K, V],
        other: dict[K, V] | Mapping[K, V] | AbstractDict[K, V],
        *,
        _coerce_keys: bool = True,
        _coerce_values: bool = True
    ) -> None:
        from type_validation import _validate_or_coerce_iterable

        validated_keys = _validate_or_coerce_iterable(other.keys(), self.key_type, _coerce=_coerce_keys)
        validated_values = _validate_or_coerce_iterable(other.values(), self.value_type, _coerce=_coerce_values)
        other_items = dict(zip(validated_keys, validated_values)).items()

        for key, value in other_items:
            self[key] = value

    def pop(
        self: AbstractMutableDict[K, V],
        key: K,
        fallback: V | None = None,
        *,
        _coerce_keys: bool = None,
        _coerce_values: bool = None
    ) -> V:
        from type_validation import _validate_or_coerce_value
        if fallback is not None:
            return self.data.pop(
                _validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys),
                _validate_or_coerce_value(fallback, self.value_type, _coerce=_coerce_values)
            )
        return self.data.pop(_validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys))

    def popitem(self: AbstractMutableDict[K, V]) -> tuple[K, V]:
        return self.data.popitem()

    def setdefault(self: AbstractMutableDict[K, V], key: K, default: V) -> V:
        from type_validation import _validate_or_coerce_value
        return self.data.setdefault(
            _validate_or_coerce_value(key, self.key_type),
            _validate_or_coerce_value(default, self.value_type)
        )
