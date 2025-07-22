from __future__ import annotations

from dataclasses import field
from functools import reduce
from typing import Iterable, Any, Callable, Mapping, TYPE_CHECKING, TypeVar, ClassVar
from collections import defaultdict

from immutabledict import immutabledict

from GenericBase import GenericBase, class_name

if TYPE_CHECKING:
    from type_validation import (
        _validate_or_coerce_value,
        _validate_or_coerce_iterable,
        _validate_collection_type_and_get_values,
        _validate_or_coerce_iterable_of_iterables,
        _infer_type_contained_in_iterable
    )


def forbid_instantiation(cls):
    """
    Class decorator that forbids direct instantiation of the given class.
    Subclasses are allowed.
    """
    original_new = cls.__new__

    def __new__(subcls, *args, **kwargs):
        if subcls is cls:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated directly.")
        return original_new(subcls, *args, **kwargs)

    cls.__new__ = staticmethod(__new__)
    return cls


@forbid_instantiation
class Collection[T](GenericBase[T]):
    """
    Abstract base class representing a generic collection of items of type T.

    Provides a foundational interface for storing and operating on collections of uniformly-typed items. It uses
    generics to enforce runtime type safety and supports fluent and functional-style operations inspired by Java's
    Stream API.

    The class enforces runtime generic type tracking using a metaclass extension (GenericBase), allowing validation
    and coercion of elements during construction and transformations. It cannot be directly instantiated and must be
    parameterized by a concrete type when the constructor is called (e.g., Collection[int]).

    :param item_type: The inferred type of elements stored in the collection, derived from the generic.
    :type item_type: type[T]
    :param values: The internal container of stored values, usually of one of Python's built-in Iterables (list, tuple,
    set, frozenset, etc.).
    :type values: Any
    """

    item_type: type[T]
    values: Any

    def __init__(
        self: Collection[T],
        *values: T,
        _coerce: bool = False,
        _forbidden_iterable_types: tuple[type, ...] = (),
        _finisher: Callable[[Iterable[T]], Any] = None,
        _skip_validation: bool = False
    ) -> None:
        """
        Basic constructor for the Collection abstract class, to be invoked by all subclasses.

        The attribute item_type is inferred from the generic with which the class was called, which was stored on the
        _args attribute of the class itself returned by __class_getitem__ and fetched by _inferred_item_type.

        :param values: Values, received as an iterable or one by one, to store in the Collection.
        :param _coerce: State parameter to force type coercion or not. Some numeric type coercions are always performed.
        :param _forbidden_iterable_types: Tuple of types that the values parameter cannot be.
        :param _finisher: Callable to be applied to the values before storing them on the values attribute of the object.
        :param _skip_validation: State parameter to skip type validation of the values. Only use it in cases where it's
        known that the values received will match the generic type.
        :raises TypeError: If the generic types weren't provided or were a TypeVar.
        :raises TypeError: If the values iterable parameter is of one of the forbidden iterable types.
        """
        from type_validation import _validate_or_coerce_iterable, _validate_type

        # Fetches the generic type of the Collection from its _args attribute inherited from GenericBase.
        generic_item_type: type = type(self)._inferred_item_type()

        # If the generic item type is None or a TypeVar, raises a TypeError.
        if generic_item_type is None:
            raise TypeError(f"{type(self).__name__} must be instantiated with a generic type, e.g., MutableList[int](...) or via .of().")

        if isinstance(generic_item_type, TypeVar):
            raise TypeError(f"{type(self).__name__} was instantiated without a generic type, somehow {generic_item_type} was a TypeVar.")

        # If the values are of length 1, the value they contain doesn't match the generic type expected but is an Iterable,
        # the tuple is unpacked.
        if len(values) == 1 and not _validate_type(values[0], generic_item_type) and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            values = values[0]

        # If values is of one of the forbidden iterable types, raises a TypeError.
        if isinstance(values, _forbidden_iterable_types):
            raise TypeError(f"Invalid type {type(values).__name__} for class {type(self).__name__}.")

        object.__setattr__(self, 'item_type', generic_item_type)

        final_values = values if _skip_validation else _validate_or_coerce_iterable(values, self.item_type, _coerce=_coerce)

        _finisher = _finisher or getattr(type(self), '_finisher', lambda x : x)

        object.__setattr__(self, 'values', _finisher(final_values))

    @classmethod
    def _inferred_item_type(cls: type[Collection[T]]) -> type[T] | None:
        """
        Returns the generic type argument T with which this Collection subclass was parameterized, or None.

        This method is used internally for runtime type enforcement and generic introspection, and it fetches the generic
        type from the _args attribute the class inherits from GenericBase which is set on its __class_getitem__ method.

        :return: The generic type T that this class was called upon, stored on its attribute _args by the __class_getitem__
        method inherited from GenericBase. If unable to retrieve it, returns None.
        """
        try:
            return cls._args[0]
        except (AttributeError, IndexError, TypeError, KeyError):
            return None

    @classmethod
    def of(cls: type[Collection], *values: T) -> Collection[T]:
        """
        Creates a Collection object containing the given values, inferring their common type.

        Acts as a type-safe factory method for dynamically constructing properly parameterized collections when the type
        is not known statically.

        :param values: One or more parameters, or an Iterable of values to initialize the new Collection with.
        :raises ValueError: If no values are provided.
        :return: A new Collection of the same type as cls containing the passed values, inferring its item_type from
        with type_validation.py's _infer_type_contained_in_iterable method.
        """
        if len(values) == 1 and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            values = tuple(values[0])
        from type_validation import _infer_type_contained_in_iterable
        return cls[_infer_type_contained_in_iterable(values)](values, _skip_validation=True)

    @classmethod
    def empty[R](cls: type[Collection], item_type: type[R]) -> Collection[R]:
        """
        Creates an empty Collection subclass of the current class, parameterized with the given item type.

        Useful for initialization of empty collections with known type context.

        :param item_type: Type of the to-be elements of the empty Collection.
        :raises ValueError: If item_type is None.
        :return: An empty Collection of the same type as cls with the given item_type.
        """
        if item_type is None:
            raise ValueError(f"Trying to call {cls.__name__}.empty with a None type.")
        return cls[item_type]()

    def __len__(self: Collection[T]) -> int:
        """
        Returns the number of elements in the Collection by delegating to the internal container's __len__ method.
        """
        return len(self.values)

    def __iter__(self: Collection[T]) -> Iterable[T]:
        """
        Returns an iterator over the values in the Collection's internal container.
        """
        return iter(self.values)

    def __contains__(self: Collection[T], item: T | Iterable[T]) -> bool:
        """
        Returns True if the provided item (or iterable of items) is contained in the Collection's internal container.

        :return: True if item is an object of the item_type of the Collection and is contained in its values, or if it's
        an Iterable whose elements are all contained on self's values. False otherwise.
        """
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            return all(i in self.values for i in item)
        return item in self.values

    def __eq__(self: Collection[T], other: Any) -> bool:
        """
        Performs structural and type-based equality comparison between two Collection instances.

        :return: True if self and other share:
        - The same subclass
        - The same item type
        - The same underlying values (compared with ==)
        False otherwise.
        """
        return (
            isinstance(other, Collection)
            and self.item_type == other.item_type
            and self.values == other.values
        )

    def __repr__(self: Collection[T]) -> str:
        """
        Returns a string representation of the Collection, showing its generic type name and contained values.
        """
        return f"{class_name(type(self))}{self.values}"

    def __bool__(self: Collection[T]) -> bool:
        """
        Implements the __bool__ dunder method delegating to the values' attribute implementation.

        :return: True if the Collection contains at least one value, False otherwise.
        """
        return bool(self.values)

    def copy(self: Collection[T], deep: bool = False) -> Collection[T]:
        """
        Returns a shallow or deep copy of the Collection.

        If the underlying values implement `.copy()`, it uses that method. Otherwise, directly references the original
        values or uses `deepcopy` if requested. Skips re-validation for performance.

        :param deep: Boolean state parameter to control if the copy is shallow or deep.
        """
        from copy import deepcopy
        values = deepcopy(self.values) if deep else (self.values.copy() if hasattr(self.values, 'copy') else self.values)
        return type(self)[self.item_type](values, _skip_validation=True)

    def to_list(self: Collection[T]) -> list[T]:
        """
        Returns the contents of the Collection as a list.
        """
        return list(self.values)

    def to_tuple(self: Collection[T]) -> tuple[T]:
        """
        Returns the contents of the Collection as a tuple.
        """
        return tuple(self.values)

    def to_set(self: Collection[T]) -> set[T]:
        """
        Returns the contents of the Collection as a set.
        """
        return set(self.values)

    def to_frozen_set(self: Collection[T]) -> frozenset[T]:
        """
        Returns the contents of the Collection as a frozenset.
        """
        return frozenset(self.values)

    def to_dict[K, V](
        self: Collection[T],
        key_mapper: Callable[[T], K] = lambda x : x,
        value_mapper: Callable[[T], V] = lambda x : x
    ) -> dict[K, V]:
        """
        Returns a dictionary obtained by calling the key and value mappers on each item of the Collection.

        :param key_mapper: Callable to obtain the keys from. Defaults to identity mapping.
        :param value_mapper: Callable to obtain the values from. Defaults to identity mapping.
        :return: A dictionary derived from the Collection by mapping each item to a (key, value) pair using the provided
        key_mapper and value_mapper callables.
        """
        return {
            key_mapper(item) : value_mapper(item)
            for item in self
        }

    def count(self: Collection[T], value: Any) -> int:
        """
        Returns the number of occurrences of the given value in the Collection.

        :param value: Value to count within the Collection.
        :return: The number of appearances of the value in the Collection. If the underlying container supports
        `.count`, it uses that method; otherwise, falls back to manual equality counting. Supports unhashable values.
        """
        try:
            return self.values.count(value)
        except (AttributeError, TypeError, ValueError):
            return sum(1 for v in self.values if v == value)


    # Functional Methods:

    def map[R](
        self: Collection[T],
        f: Callable[[T], R],
        result_type: type[R] | None = None,
        *,
        _coerce: bool = False
    ) -> Collection[R]:
        """
        Maps each value of the Collection to its image by the function `f` and returns a new Collection of them.

        :param f: Callable object to map the Collection with.
        :param result_type: Type expected to be returned by the Callable.
        :param _coerce: State parameter to try to force coercion to the expected result type if it's not None.
        :return: A new Collection of the same type as self containing those values. If result_type is given, it is used
        as the type of the returned Collection, if not that is inferred.
        """
        mapped_values = [f(value) for value in self.values]
        return (
            type(self)[result_type](mapped_values, _coerce=_coerce) if result_type is not None
            else type(self).of(mapped_values)
        )

    def flatmap[R](
        self: Collection[T],
        f: Callable[[T], Iterable[R]],
        result_type: type[R] | None = None,
        *,
        _coerce: bool = False
    ) -> Collection[R]:
        """
        Maps and flattens each element of the Collection and returns a new Collection containing the results.

        :param f: Callable object to map the Collection with.
        :type f: Callable[[T], Iterable[R]]
        :param result_type: Type of Iterable expected to be returned by the Callable.
        :type result_type: type[R] | None
        :param _coerce: State parameter to try to force coercion to the expected result type if it's not None.
        :return: A new Collection of the same type as self containing those values. If result_type is given, it is used
        as the type of the returned Collection, if not that is inferred. Requires that `f` returns an iterable
        (excluding str and bytes) for each element.
        :rtype: Collection[R]
        """

        flattened = []
        for value in self.values:
            result = f(value)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        return type(self)[result_type](flattened, _coerce=_coerce) if result_type is not None else type(self).of(flattened)

    def filter(self: Collection[T], predicate: Callable[[T], bool]) -> Collection[T]:
        """
        Filter the collection by a predicate function.

        :param predicate: A function from T to the booleans that the kept values will satisfy.
        :type predicate: Callable[[T], bool]
        :return: A filtered collection containing only the values that were evaluated to True by the predicate.
        :rtype: Collection[T]
        """
        return type(self)([value for value in self.values if predicate(value)], _skip_validation=True)

    def all_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if all elements in the collection satisfy the given predicate.

        :param predicate: A function from T to the booleans.
        :type predicate: Callable[[T], bool]
        :return: True if all elements match the predicate, False otherwise.
        :rtype: bool
        """
        return all(predicate(value) for value in self.values)

    def any_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if any element in the collection satisfies the given predicate.

        :param predicate: A function from T to the booleans.
        :type predicate: Callable[[T], bool]
        :return: True if at least one element matches the predicate, False otherwise.
        :rtype: bool
        """
        return any(predicate(value) for value in self.values)

    def none_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if no element in the collection satisfies the given predicate.

        :param predicate: A function from T to the booleans.
        :type predicate: Callable[[T], bool]
        :return: True if no elements match the predicate, False otherwise.
        :rtype: bool
        """
        return not any(predicate(value) for value in self.values)

    def reduce(self: Collection[T], f: Callable[[T, T], T], unit: T | None = None) -> T:
        """
        Reduces the collection to a single value using a binary operator function and an optional initial unit.

        :param f: A function that combines two elements of type T into one.
        :type f: Callable[[T, T], T]
        :param unit: Optional initial value for the reduction. If provided, the reduction starts with this.
        :type unit: T | None
        :return: The result of the reduction, as done after being delegated to the reduce() function applied to the
        internal container.
        :rtype: T
        """
        if unit is not None:
            return reduce(f, self.values, unit)
        return reduce(f, self.values)

    def for_each(self: Collection[T], consumer: Callable[[T], None]) -> None:
        """
        Performs the given consumer function on each element in the collection.

        :param consumer: A function that takes an element of type T and returns None.
        :type consumer: Callable[[T], None]
        """
        for value in self.values:
            consumer(value)

    def peek(self: Collection[T], consumer: Callable[[T], None]) -> Collection[T]:
        """
        Performs the given consumer function on each element for side effects and returns the original collection.

        :param consumer: A function that takes an element of type T and returns None.
        :type consumer: Callable[[T], None]
        :return: The original collection (self).
        :rtype: Collection[T]
        """
        for item in self.values:
            consumer(item)
        return self

    def distinct[K](self: Collection[T], key: Callable[[T], K] = lambda x: x) -> Collection[T]:
        """
        Returns a new collection with only distinct elements, determined by a key function.

        :param key: A function mapping each element to a hashable key. Defaults to identity mapping.
        :type key: Callable[[T], K]
        :return: A Collection of the same type as self with duplicates removed based on the key.
        :rtype: Collection[T]
        """
        seen = set()
        result = []
        for value in self.values:
            key_of_value = key(value)
            if key_of_value not in seen:
                seen.add(key_of_value)
                result.append(value)
        return type(self)(result, _skip_validation=True)

    def max(self: Collection[T], *, default: T | None = None, key: Callable[[T], Any] = None) -> T | None:
        """
        Returns the maximum element in the collection, optionally using a key function or default value.

        :param default: A value to return if the collection is empty.
        :type default: T | None
        :param key: A function to extract a comparison key from each element.
        :type key: Callable[[T], Any], optional
        :return: The maximum element, or default if provided and self is empty.
        :rtype: T | None
        """
        if default is not None:
            return max(self.values, default=default, key=key)
        if not self.values:
            return None
        return max(self.values, key=key)

    def min(self: Collection[T], *, default: T | None = None, key: Callable[[T], Any] = None) -> T | None:
        """
        Returns the minimum element in the collection, optionally using a key function or default.

        :param default: A value to return if the collection is empty.
        :type default: T | None
        :param key: A function to extract a comparison key from each element.
        :type key: Callable[[T], Any], optional
        :return: The minimum element, or default if provided and self is empty.
        :rtype: T | None
        """
        if default is not None:
            return min(self.values, default=default, key=key)
        if not self.values:
            return None
        return min(self.values, key=key)

    def group_by[K](
        self: Collection[T],
        key: Callable[[T], K]
    ) -> dict[K, Collection[T]]:
        """
        Groups the items in the Collection on a dict by their value by the key function.

        :param key: Callable to group the items by.
        :return: A dict mapping each found value of key onto a Collection of the same type as self containing the items
        in the original Collection that were mapped to that value by the key function.
        """
        groups: dict[K, list[T]] = defaultdict(list)
        for item in self.values:
            groups[key(item)].append(item)
        return {
            key : type(self)[self.item_type](group, _skip_validation=True)
            for key, group in groups.items()
        }

    def partition_by(
        self: Collection[T],
        predicate: Callable[[T], bool]
    ) -> dict[bool, Collection[T]]:
        """
        A specialized binary version of group_by grouping by a predicate to bool.

        :param predicate: Function from T to the booleans to partition the Collection by.
        :type predicate: Callable[[T], bool]
        :return: A dict whose True key is mapped to a Collection of the same type as self containing all items in it
        that satisfied the predicate, likewise for False.
        """
        return self.group_by(predicate)

    def collect[A, R](
        self: Collection[T],
        supplier: Callable[[], A],
        accumulator: Callable[[A, T], None],
        finisher: Callable[[A], R] = lambda x : x
    ) -> R:
        """
        Generalized collector, replicating Java's Stream API .collect method.

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]
        :param accumulator: Accepts (accumulator, item) to process each item.
        :type accumulator: Callable[[A, T], None]
        :param finisher: Final transformation to obtain a result. Defaults to identity mapping.
        :type finisher: Callable[[A], R]
        :return: The collected result.
        """
        acc = supplier()
        for item in self.values:
            accumulator(acc, item)
        return finisher(acc)

    def stateful_collect[A, S, R](
        self: Collection[T],
        supplier: Callable[[], A],
        state_supplier: Callable[[], S],
        accumulator: Callable[[A, T, S], None],
        finisher: Callable[[A, S], R] = lambda x, _: x
    ) -> R:
        """
        A generalized collector with internal state, inspired by Java's Stream API.

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]
        :param state_supplier: Provides the initial state object.
        :type state_supplier: Callable[[], S]
        :param accumulator: Accepts (accumulator, item, state) to process each item.
        :type accumulator: Callable[[A, T, S], None]
        :param finisher: Final transformation combining accumulator and state to a result.
        :type finisher: Callable[[A, S], R]
        :return: The final collected result.
        """
        acc = supplier()
        state = state_supplier()
        for item in self.values:
            accumulator(acc, item, state)
        return finisher(acc, state)


@forbid_instantiation
class AbstractSequence[T](Collection[T]):
    """
    Abstract base class for sequence-like collections with ordering and indexing capabilities.

    Provides standard sequence operations such as indexing, slicing, comparison, addition, multiplication, and sorting.
    Must be subclassed to create concrete implementations.

    This class will be further extended by `AbstractMutableSequence` to add the methods that modify the internal data
    container of the class.

    WIP
    """

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = tuple

    def __getitem__(self: AbstractSequence[T], index: int | slice) -> T | AbstractSequence[T]:
        """
        Returns the item at the given index or a new sliced sequence.

        :param index: An integer index or slice object.
        :type index: int | slice
        :return: The item at the given index or a new sliced sequence.
        :rtype: T | AbstractSequence[T]
        :raises TypeError: If index is not an int or slice.
        """
        if isinstance(index, slice):
            return type(self)[self.item_type](self.values[index])
        elif isinstance(index, int):
            return self.values[index]
        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __eq__(self: AbstractSequence[T], other: Any) -> bool:
        """
        Checks equality with another `AbstractSequence` based on their item type and values.

        :param other: Object to compare against.
        :type other: Any
        :return: True if both have the same item type and the same values on the same order.
        :rtype: bool
        """
        return (
            isinstance(other, AbstractSequence)
            and self.item_type == other.item_type
            and list(self.values) == list(other.values)
        )

    def __lt__(self: AbstractSequence[T], other) -> bool:
        """
        Checks if this sequence is lexicographically less than another.

        :param other: Another sequence or iterable.
        :type other: AbstractSequence | list | tuple
        :return: True if less than `other`.
        :rtype: bool
        """
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
        return self.filter(lambda item : item not in other)

    def __reversed__(self: AbstractSequence[T]):
        return reversed(self.values)

    def reversed(self) -> AbstractSequence[T]:
        return type(self)(reversed(self.values), _skip_validation=True)

    def index(self: AbstractSequence[T], value) -> int:
        return self.values.index(value)

    def sorted(self: AbstractSequence[T], key=None, reverse=False) -> AbstractSequence[T]:
        return type(self)(sorted(self.values, key=key, reverse=reverse), _skip_validation=True)


@forbid_instantiation
class AbstractMutableSequence[T](AbstractSequence[T]):

    _finisher: Callable[[Iterable[T]], Iterable[T]] = list
    _mutable: bool = True

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

    def insert(self, index: int, value: T, *, _coerce: bool = False) -> None:
        from type_validation import _validate_or_coerce_value
        self.values.insert(index, _validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def extend(self, other: Iterable[T], *, _coerce: bool = False) -> None:
        from type_validation import _validate_or_coerce_iterable
        self.values.extend(_validate_or_coerce_iterable(other, self.item_type, _coerce=_coerce))

    def pop(self, index: int = -1) -> T:
        return self.values.pop(index)

    def remove(
        self: AbstractSequence[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value
        if _coerce:
            try:
                value = _validate_or_coerce_value(value, self.item_type)
            except (TypeError, ValueError):
                pass
        self.values.remove(value)


@forbid_instantiation
class AbstractSet[T](Collection[T]):

    _finisher: Callable[[Iterable[T]], Iterable[T]] = frozenset

    def __eq__(self: AbstractSet[T], other: Any) -> bool:
        return (
            isinstance(other, AbstractSet)
            and self.item_type == other.item_type
            and set(self.values) == set(other.values)
        )

    def __lt__(self: AbstractSet[T], other: Any) -> bool:
        if isinstance(other, AbstractSet):
            return self.values < other.values
        return NotImplemented

    def __le__(self: AbstractSet[T], other: Any) -> bool:
        if isinstance(other, AbstractSet):
            return self.values <= other.values
        return NotImplemented

    def __gt__(self: AbstractSet[T], other: Any) -> bool:
        if isinstance(other, AbstractSet):
            return self.values > other.values
        return NotImplemented

    def __ge__(self: AbstractSet[T], other: Any) -> bool:
        if isinstance(other, AbstractSet):
            return self.values >= other.values
        return NotImplemented

    def __or__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        return type(self)(self.values | other.values)

    def __and__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        return type(self)(self.values & other.values)

    def __sub__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        return type(self)(self.values - other.values)

    def __xor__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        return type(self)(self.values ^ other.values)

    def union(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
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


@forbid_instantiation
class AbstractMutableSet[T](AbstractSet[T]):

    _finisher: Callable[[Iterable[T]], Iterable[T]] = set
    _mutable: bool = True

    def __ior__(self: AbstractMutableSet[T], other: AbstractSet[T]) -> AbstractMutableSet[T]:
        self.values |= other.values
        return self

    def __iand__(self: AbstractMutableSet[T], other: AbstractSet[T]) -> AbstractMutableSet[T]:
        self.values &= other.values
        return self

    def __isub__(self: AbstractMutableSet[T], other: AbstractSet[T]) -> AbstractMutableSet[T]:
        self.values -= other.values
        return self

    def __ixor__(self: AbstractMutableSet[T], other: AbstractSet[T]) -> AbstractMutableSet[T]:
        self.values ^= other.values
        return self

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
                value = _validate_or_coerce_value(value, self.item_type)
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
                value = _validate_or_coerce_value(value, self.item_type)
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


@forbid_instantiation
class AbstractDict[K, V](GenericBase[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __init__(
        self: AbstractDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None,
        _coerce_keys: bool = False,
        _coerce_values: bool = False,
        _finisher: Callable[[dict[K, V]], Any] = None,
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
            raise TypeError(f"Generic types must be fully specified for {type(self).__name__}. Use {type(self)._origin.__name__}.of(...) to infer types from iterable.")

        object.__setattr__(self, "key_type", key_type)
        object.__setattr__(self, "value_type", value_type)

        _finisher = _finisher or getattr(type(self), '_finisher', lambda x: x)

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
    def of(
        cls: type[AbstractDict[K, V]],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]
    ) -> AbstractDict[K, V]:
        if keys_values is None or not keys_values:
            raise ValueError(f"Can't create a {cls.__name__} object from empty iterable.")
        from type_validation import _infer_type_contained_in_iterable, _split_keys_values
        keys, values, _ = _split_keys_values(keys_values)
        key_type = _infer_type_contained_in_iterable(keys)
        value_type = _infer_type_contained_in_iterable(values)
        return cls[key_type, value_type](_keys=keys, _values=values)

    @classmethod
    def of_keys_values(
        cls: type[AbstractDict[K, V]],
        keys: Iterable[K],
        values: Iterable[V]
    ) -> AbstractDict[K, V]:
        keys = list(keys)
        values = list(values)

        if len(keys) != len(values):
            raise ValueError("Keys and iterable must be of the same length when using .of_keys_values")

        from type_validation import _infer_type_contained_in_iterable
        key_type = _infer_type_contained_in_iterable(keys)
        value_type = _infer_type_contained_in_iterable(values)
        return cls[key_type, value_type](_keys=keys, _values=values)

    def __getitem__(self: AbstractDict[K, V], key: K | slice) -> V | AbstractDict[K, V]:
        """
        Returns its assigned value if key is of type K, or if it's a slice, the AbstractDict of the same type as self
        constructed by taking all the keys that fall on that slice.
        :param key: Key or slice to get.
        :return: The value assigned to the key, or the subdict of all the keys falling on the slice.
        """
        if isinstance(key, slice):
            # Subdict slicing
            if key.step is not None:
                raise TypeError("Step is not supported in dict slicing.")

            start, stop = key.start, key.stop

            sample_key: K | None = next(iter(self.data), None)
            if sample_key is None:
                return type(self)({})

            try:
                # Try comparing sample_key with start/stop if provided
                if start is not None:
                    sample_key >= start
                if stop is not None:
                    sample_key <= stop
            except TypeError:
                raise TypeError("Keys must support ordering for subdict slicing.")

            return self.filter_keys(
                lambda k: (start is None or start <= k) and (stop is None or k <= stop)
            )
        else:
            # Regular key access
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
            isinstance(other, AbstractDict)
            and self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def __repr__(self: AbstractDict[K, V]) -> str:
        return f"{class_name(type(self))}{dict(self.data)}"

    def __or__(self: AbstractDict[K, V], other: Mapping[K, V]) -> AbstractDict[K, V]:
        return type(self)(dict(self.data) | dict(other))

    def __and__(self: AbstractDict[K, V], other: Mapping[K, V]) -> AbstractDict[K, V]:
        return type(self)({k: self.data[k] for k in self.data.keys() & other.keys()})

    def __sub__(self: AbstractDict[K, V], other: Mapping[K, V]) -> AbstractDict[K, V]:
        return type(self)({k: v for k, v in self.data.items() if k not in other})

    def __xor__(self: AbstractDict[K, V], other: Mapping[K, V]) -> AbstractDict[K, V]:
        sym_keys = self.data.keys() ^ other.keys()
        return type(self)({k: (self.data.get(k) or other.get(k)) for k in sym_keys})

    def to_dict(self: AbstractDict[K, V]) -> dict[K, V]:
        return dict(self.data)

    def to_immutable_dict(self: AbstractDict[K, V]) -> immutabledict[K, V]:
        return immutabledict(self.data)

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
        try:
            return self.data[key]
        except KeyError:
            return (
                _validate_or_coerce_value(fallback, self.value_type, _coerce=_coerce_values)
                if fallback is not None
                else None
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


@forbid_instantiation
class AbstractMutableDict[K, V](AbstractDict[K, V]):

    _finisher: Callable[[dict[K, V]], Mapping[K, V]] = immutabledict
    _mutable: bool = True

    def __setitem__(self: AbstractMutableDict[K, V], key: K, value: V) -> None:
        from type_validation import _validate_or_coerce_value
        self.data[_validate_or_coerce_value(key, self.key_type)] = _validate_or_coerce_value(value, self.value_type)

    def __delitem__(self: AbstractMutableDict[K, V], key: K) -> None:
        del self.data[key]

    def clear(self: AbstractMutableDict[K, V]) -> None:
        self.data.clear()

    def __ior__(self: AbstractMutableDict[K, V], other: Mapping[K, V]) -> AbstractMutableDict[K, V]:
        self.update(other)
        return self

    def __iand__(self: AbstractMutableDict[K, V], other: Mapping[K, V]) -> AbstractMutableDict[K, V]:
        keys_to_remove = set(self.data) - set(other)
        for key in keys_to_remove:
            del self.data[key]
        return self

    def __isub__(self: AbstractMutableDict[K, V], other: Mapping[K, V]) -> AbstractMutableDict[K, V]:
        for key in other:
            self.data.pop(key, None)
        return self

    def __ixor__(self: AbstractMutableDict[K, V], other: Mapping[K, V]) -> AbstractMutableDict[K, V]:
        for key in other:
            if key in self.data:
                del self.data[key]
            else:
                self.data[key] = other[key]
        return self

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
