from __future__ import annotations

from dataclasses import field
from functools import reduce
from typing import Iterable, Any, Callable, Mapping, TYPE_CHECKING, TypeVar, ClassVar, Iterator
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
    Class decorator that forbids direct instantiation of the given class with or without generics.

    :raises TypeError: If the decorated class is instantiated directly, but allows instantiation of its subclasses.
    """

    def __new__(subcls, *args, **kwargs):
        if getattr(subcls, "_origin", None) is cls:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated, even with generics.")
        if subcls is cls:
            raise TypeError(f"{cls.__name__} is an abstract class and cannot be instantiated directly.")
        return object.__new__(subcls)

    cls.__new__ = staticmethod(__new__)
    return cls


@forbid_instantiation
class Collection[T](GenericBase[T]):
    """
    Abstract base class representing a collection of items of type T, wrapping an underlying container and its type.

    Provides a base class for storing and operating on collections of items with a common type, without any further
    structure, which will be added on certain extensions. It uses generics to enforce runtime type safety and supports
    fluent and functional-style operations inspired by Java's Stream API.

    The class enforces runtime generic type tracking using the metaclass extension GenericBase, from which it inherits
    its __class_getitem__ method, which stores the generic types the Collection subclasses are called upon on an _args
    attribute, and that base subclass as an _origin attribute of a new dynamic subclass, which can then be used to
    instantiate new objects, or perform type validation with full access to the generic types.

    It is an abstract class and cannot be directly instantiated. Its subclasses must be parameterized by a concrete type
    when the constructor is called (e.g., MutableList[int]).

    Attributes:
        item_type (type[T]): The inferred type of elements stored in the collection, derived from the generic types.

        values (Any): The internal container of stored values, usually of one of Python's built-in Iterables.

        _finisher (ClassVar[Callable]): A function that is applied to the values during __init__ before setting it as the
        attribute of the object. It's generally used to transform them into another Iterable type. If missing, it's
        assumed to be the identity mapping on Collection's __init__ method.

    Note:
        Any method that returns a new Collection instance (e.g., filter, union, sorted, etc.) constructs the returned
        value using type(self)(...). This ensures that:

            - The returned object has the same concrete runtime subclass as self.
            - Generic type parameters (T) are preserved without reapplying __class_getitem__, because they are
              already bound via the dynamic subclassing mechanism in __class_getitem__.

        This makes behavior consistent across all subclasses of Collection: type(self) guarantees the returned value
        matches the exact type and structure of self, unless otherwise explicitly overridden. Also, calling
        type(self)[another_item_type] correctly creates a new dynamic subclass with the same base class as self but
        with the new generic type.
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

        The attribute item_type is inferred from the generic the class was called upon, which was stored on the
        _args attribute of the class returned by __class_getitem__ and fetched by _inferred_item_type.

        :param values: Values, received as an iterable or one by one, to store in the Collection.
        :type values: T

        :param _coerce: State parameter to force type coercion or not. Some numeric type coercions are always performed.
        :type _coerce: bool

        :param _forbidden_iterable_types: Tuple of types that the values parameter cannot be.
        :type _forbidden_iterable_types: tuple[type, ...]

        :param _finisher: Callable to be applied to the values before storing them on the values attribute of the object.
        Defaults to None, and in that case is later assigned to the identity mapping.
        :type _finisher: Callable[[Iterable[T]], Any]

        :param _skip_validation: State parameter to skip type validation of the values. Only use it in cases where it's
        known that the values received will match the generic type.
        :type _skip_validation: bool

        :raises TypeError: If the generic type wasn't provided or was a TypeVar.
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

        :return: The generic type T that this class was called upon, as stored on its attribute _args by the
        __class_getitem__ method inherited from GenericBase. If unable to retrieve it, returns None.
        :rtype: type[T] | None
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
        :type values: T

        :return: A new Collection that is an instance of cls containing the passed values, inferring its item_type from
        _infer_type_contained_in_iterable method.
        :rtype: Collection[T]

        :raises ValueError: If no values are provided.
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
        :type item_type: type[R]

        :return: An empty Collection that is an instance of cls with the given item_type.
        :rtype: Collection[R]

        :raises ValueError: If item_type is None.
        """
        if item_type is None:
            raise ValueError(f"Trying to call {cls.__name__}.empty with a None type.")
        return cls[item_type]()

    def __len__(self: Collection[T]) -> int:
        """
        Returns the number of elements in the Collection by delegating to the internal container's __len__ method.

        :return: The length of the internal container.
        :rtype: int
        """
        return len(self.values)

    def __iter__(self: Collection[T]) -> Iterator[T]:
        """
        Returns an iterator over the values in the Collection's internal container.

        :return: An iterable over the values of the Collection.
        :rtype: Iterator[T]
        """
        return iter(self.values)

    def __contains__(self: Collection[T], item: T | Iterable[T]) -> bool:
        """
        Returns True if the provided item (or iterable of items) is contained in the Collection's internal container.

        :return: True if item is an object of the item_type of the Collection and is contained in its values, or if it's
        an Iterable whose elements are all contained on self's values. False otherwise.
        :rtype: bool
        """
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            return all(i in self.values for i in item)
        return item in self.values

    def __eq__(self: Collection[T], other: Any) -> bool:
        """
        Checks if two Collections are equal comparing their values and item type.

        If each Collection has a different internal container, they won't be equal unless those containers are designed
        to be compatible, like set and frozenset, but unlike list and tuple.

        :return: True if self and other share the same subclass, item type and underlying values (compared with ==),
        False otherwise.
        :rtype: bool
        """
        return (
            isinstance(other, Collection)
            and self.item_type == other.item_type
            and self.values == other.values
        )

    def __repr__(self: Collection[T]) -> str:
        """
        Returns a string representation of the Collection, showing its generic type name and contained values.

        :return: A string representation of the object.
        :rtype: str
        """
        return f"{class_name(type(self))}{self.values}"

    def __bool__(self: Collection[T]) -> bool:
        """
        Returns a boolean interpretation of the Collection delegating to the underlying container's __bool__ method.

        :return: True if the Collection contains at least one value, False otherwise.
        :rtype: bool
        """
        return bool(self.values)

    def copy(self: Collection[T], deep: bool = False) -> Collection[T]:
        """
        Returns a shallow or deep copy of the Collection.

        If the underlying values implement `.copy()`, it uses that method. Otherwise, directly references the original
        values or uses `deepcopy` if requested. Skips re-validation for performance.

        :param deep: Boolean state parameter to control if the copy is shallow or deep.
        :return: A shallow or deep copy of the object.
        :rtype: Collection[T]
        """
        from copy import deepcopy
        values = deepcopy(self.values) if deep else (self.values.copy() if hasattr(self.values, 'copy') else self.values)
        return type(self)(values, _skip_validation=True)

    def to_list(self: Collection[T]) -> list[T]:
        """
        Returns the contents of the Collection as a list.

        :return: A list containing the values of the Collection.
        :rtype: list[T]
        """
        return list(self.values)

    def to_tuple(self: Collection[T]) -> tuple[T]:
        """
        Returns the contents of the Collection as a tuple.

        :return: A tuple containing the values of the Collection.
        :rtype: tuple[T]
        """
        return tuple(self.values)

    def to_set(self: Collection[T]) -> set[T]:
        """
        Returns the contents of the Collection as a set.

        :return: A set containing the values of the Collection.
        :rtype: set[T]
        """
        return set(self.values)

    def to_frozen_set(self: Collection[T]) -> frozenset[T]:
        """
        Returns the contents of the Collection as a frozenset.

        :return: A frozenset containing the values of the Collection.
        :rtype: frozenset[T]
        """
        return frozenset(self.values)

    def to_dict[K, V](
        self: Collection[T],
        key_mapper: Callable[[T], K] = lambda x : x,
        value_mapper: Callable[[T], V] = lambda x : x
    ) -> dict[K, V]:
        """
        Returns a dictionary obtained by calling the key and value mappers on each item of the Collection.

        :param key_mapper: Function to obtain the keys from. Defaults to identity mapping.
        :type key_mapper: Callable[[T], K]

        :param value_mapper: Function to obtain the values from. Defaults to identity mapping.
        :type value_mapper: Callable[[T], V]

        :return: A dictionary derived from the Collection by mapping each item to a (key, value) pair using the provided
        key_mapper and value_mapper callables.
        :rtype: dict[K, V]
        """
        return {
            key_mapper(item) : value_mapper(item)
            for item in self
        }

    def count(self: Collection[T], value: T) -> int:
        """
        Returns the number of occurrences of the given value in the Collection.

        :param value: Value to count within the Collection.
        :type value: T

        :return: The number of appearances of the value in the Collection. If the underlying container supports
        `.count`, it uses that method; otherwise, falls back to manual equality counting. Supports unhashable values.
        :rtype: int
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
        :type f: Callable[[T], R]

        :param result_type: Type expected to be returned by the Callable. If None, it will be inferred.
        :type result_type: type[R] | None

        :param _coerce: State parameter that if True, tries to coerce results to the result_type if it's not None.
        :type _coerce: bool

        :return: A new Collection of the same subclass as self containing those values. If result_type is given,
        it is used as the item_type of the returned Collection, if not that is inferred from the mapped values.
        :rtype: Collection[R]
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

        Requires that f returns an iterable (excluding str and bytes) for each element.

        :param f: Callable object to map the Collection with.
        :type f: Callable[[T], Iterable[R]]

        :param result_type: Type of Iterable expected to be returned by the Callable. If None, it will be inferred.
        :type result_type: type[R] | None

        :param _coerce: State parameter to try to force coercion to the expected result type if it's not None.
        :type _coerce: bool

        :return: A new Collection of the same subclass as self containing those values. If result_type is given,
        it is used as the type of the returned Collection, if not that is inferred.
        :rtype: Collection[R]
        """
        flattened = []
        for value in self.values:
            result = f(value)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        return (
            type(self)[result_type](flattened, _coerce=_coerce) if result_type is not None
            else type(self).of(flattened)
        )

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
        Returns True if all elements in the Collection satisfy the given predicate.

        :param predicate: A function from T to the booleans.
        :type predicate: Callable[[T], bool]

        :return: True if all elements match the predicate, False otherwise.
        :rtype: bool
        """
        return all(predicate(value) for value in self.values)

    def any_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if any element in the Collection satisfies the given predicate.

        :param predicate: A function from T to the booleans.
        :type predicate: Callable[[T], bool]

        :return: True if at least one element matches the predicate, False otherwise.
        :rtype: bool
        """
        return any(predicate(value) for value in self.values)

    def none_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if no element in the Collection satisfies the given predicate.

        :param predicate: A function from T to the booleans.
        :type predicate: Callable[[T], bool]

        :return: True if no elements match the predicate, False otherwise.
        :rtype: bool
        """
        return not any(predicate(value) for value in self.values)

    def reduce(self: Collection[T], f: Callable[[T, T], T], unit: T | None = None) -> T:
        """
        Reduces the Collection to a single value using a binary operator function and an optional initial unit.

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
        Performs the given consumer function on each element in the Collection.

        :param consumer: A function that takes an element of type T and returns None.
        :type consumer: Callable[[T], None]
        """
        for value in self.values:
            consumer(value)

    def peek(self: Collection[T], consumer: Callable[[T], None]) -> Collection[T]:
        """
        Performs the given consumer function on each element for side effects and returns the original Collection.

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
        Returns a new Collection with only distinct elements, determined by a key function.

        :param key: A function to extract a comparison key from each element. Defaults to identity mapping.
        :type key: Callable[[T], K]

        :return: A Collection of the same dynamic subclass as self with duplicates removed based on the key.
        :rtype: Collection[T]
        """
        result = []
        seen_hashable = set()
        seen_unhashable = []
        using_set = True

        for value in self.values:
            key_of_value = key(value)
            if using_set:
                try:
                    if key_of_value not in seen_hashable:
                        seen_hashable.add(key_of_value)
                        result.append(value)
                except TypeError:
                    using_set = False
                    seen_unhashable = [*seen_hashable]
                    if key_of_value not in seen_unhashable:
                        seen_unhashable.append(key_of_value)
                        result.append(value)
            else:
                if key_of_value not in seen_unhashable:
                    seen_unhashable.append(key_of_value)
                    result.append(value)

        return type(self)(result, _skip_validation=True)

    def max(self: Collection[T], *, default: T | None = None, key: Callable[[T], Any] = None) -> T | None:
        """
        Returns the maximum element in the collection, optionally using a key function or default value.

        :param default: A value to return if the collection is empty.
        :type default: T | None

        :param key: A function to extract a comparison key from each element.
        :type key: Callable[[T], Any]

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
        :type key: Callable[[T], K]

        :return: A dict mapping each value of key onto a Collection of the same dynamic subclass as self containing the
        items that were mapped to that value by the key function.
        :rtype: dict[K, Collection[T]]
        """
        groups: dict[K, list[T]] = defaultdict(list)
        for item in self.values:
            groups[key(item)].append(item)
        return {
            key : type(self)(group, _skip_validation=True)
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

        :return: A dict whose True key is mapped to a Collection of the same dynamic subclass as self containing all
        items in it that satisfied the predicate, likewise for False.
        :rtype: dict[bool, Collection[T]]
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

        The supplier gives the initial container for the result. For each item in self, the accumulator is called on
        that container and that item to process the item, then the finisher is applied to the container before returning.

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]

        :param accumulator: Accepts (container, item) to process each item via secondary effects.
        :type accumulator: Callable[[A, T], None]

        :param finisher: Final transformation to obtain a result. Defaults to identity mapping.
        :type finisher: Callable[[A], R]

        :return: The collected result.
        :rtype: R
        """
        acc = supplier()
        for item in self.values:
            accumulator(acc, item)
        return finisher(acc)

    def collect_pure[A, R](
        self: Collection[T],
        supplier: Callable[[], A],
        accumulator: Callable[[A, T], A],
        finisher: Callable[[A], R] = lambda x: x
    ) -> R:
        """
        Generalized collector, replicating Java's Stream API .collect method. The accumulator is now a pure function.

        The supplier an initial value of type A. For each item in self, the accumulator is called on that value and that
        item to process the item and update the value, then the finisher is applied to the last value before returning.

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]

        :param accumulator: Accepts (container, item) to process each item and return an updated container.
        :type accumulator: Callable[[A, T], A]

        :param finisher: Final transformation to obtain a result. Defaults to identity mapping.
        :type finisher: Callable[[A], R]

        :return: The collected result.
        :rtype: R
        """
        acc = supplier()
        for item in self.values:
            acc = accumulator(acc, item)
        return finisher(acc)

    def stateful_collect[A, S, R](
        self: Collection[T],
        supplier: Callable[[], A],
        state_supplier: Callable[[], S],
        accumulator: Callable[[A, S, T], None],
        finisher: Callable[[A, S], R] = lambda x, _: x
    ) -> R:
        """
        A generalized collector with internal state, inspired by Java's Stream API.

        The supplier gives the initial container for the result. The state_supplier the initial value for the state.
        For each item in self, the accumulator is called on the container, item and state to process the item and
        modify the state, or not, then the finisher is applied to the container and state before returning.

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]

        :param state_supplier: Provides the initial state object.
        :type state_supplier: Callable[[], S]

        :param accumulator: Accepts (accumulator, item, state) to process each item via secondary effects.
        :type accumulator: Callable[[A, S, T], None]

        :param finisher: Final transformation combining accumulator and state to a result.
        :type finisher: Callable[[A, S], R]

        :return: The final collected result.
        :rtype: R
        """
        '''
        acc = supplier()
        state = state_supplier()
        for item in self.values:
            accumulator(acc, state, item)
        return finisher(acc, state)
        '''
        return self.collect(
            supplier=lambda:(supplier(), state_supplier()),
            accumulator=lambda acc_state, item : accumulator(*acc_state, item),
            finisher=lambda acc_state : finisher(*acc_state)
        )

    def stateful_collect_pure[A, S, R](
        self: Collection[T],
        supplier: Callable[[], A],
        state_supplier: Callable[[], S],
        accumulator: Callable[[A, S, T], tuple[A, S]],
        finisher: Callable[[A, S], R] = lambda x, _: x
    ) -> R:
        """
        A generalized collector with internal state, inspired by Java's Stream API.

        The supplier provides an initial value of type A. The state_supplier the initial value of type S for the state.
        For each item in self, the accumulator is called on the container, item and state to process the item and
        return the value and state, then the finisher is applied to the last value and state before returning.

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]

        :param state_supplier: Provides the initial state object.
        :type state_supplier: Callable[[], S]

        :param accumulator: Accepts (accumulator, item, state) to process each item.
        :type accumulator: Callable[[A, S, T], tuple[A, S]]

        :param finisher: Final transformation combining accumulator and state to a result.
        :type finisher: Callable[[A, S], R]

        :return: The final collected result.
        :rtype: R
        """
        '''
        acc = supplier()
        state = state_supplier()
        for item in self.values:
            acc, state = accumulator(acc, item, state)
        return finisher(acc, state)
        '''
        return self.collect_pure(
            supplier=lambda: (supplier(), state_supplier()),
            accumulator=lambda acc_state, item: accumulator(*acc_state, item),
            finisher=lambda acc_state: finisher(*acc_state)
        )

@forbid_instantiation
class AbstractSequence[T](Collection[T]):
    """
    Abstract base class for sequence-like Collections of a type T, with ordering and indexing capabilities.

    Provides standard sequence operations such as indexing, slicing, comparison, addition of other sequences,
    multiplication by integers, and sorting. It is still an abstract class, so it must be subclassed to create concrete
    implementations.

    This class will be further extended by AbstractMutableSequence to add the methods that modify the internal data
    container of the class.

    This class sets the ClassVar attribute _finisher to tuple to ensure the immutability of the internal container.
    """

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = tuple

    def __getitem__(self: AbstractSequence[T], index: int | slice) -> T | AbstractSequence[T]:
        """
        Returns the item at the given index or a new sliced AbstractSequence.

        :param index: An integer index or slice object.
        :type index: int | slice

        :return: The item at the given index or a new AbstractSequence of the same dynamic subclass as self containing
        the sliced values.
        :rtype: T | AbstractSequence[T]

        :raises TypeError: If index is not an int or slice.
        """
        if isinstance(index, slice):
            return type(self)(self.values[index])
        elif isinstance(index, int):
            return self.values[index]
        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __eq__(self: AbstractSequence[T], other: Any) -> bool:
        """
        Checks equality with another sequence based on their item type and values.

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

    def __lt__(self: AbstractSequence[T], other: AbstractSequence[T] | list[T] | tuple[T, ...]) -> bool:
        """
        Checks if this sequence is lexicographically less than another.

        :param other: Another sequence to compare with.
        :type other: AbstractSequence[T] | list[T] | tuple[T, ...]

        :return: True if self is less than `other`.
        :rtype: bool
        """
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) < tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __gt__(self: AbstractSequence[T], other: AbstractSequence[T] | list[T] | tuple[T, ...]) -> bool:
        """
        Checks if this sequence is lexicographically greater than another.

        :param other: Another sequence to compare with.
        :type other: AbstractSequence[T] | list[T] | tuple[T, ...]

        :return: True if self is greater than `other`.
        :rtype: bool
        """
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) > tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __le__(self: AbstractSequence[T], other: AbstractSequence[T] | list[T] | tuple[T, ...]) -> bool:
        """
        Checks if this sequence is less than or equal to another.

        :param other: Another sequence to compare with.
        :type other: AbstractSequence[T] | list[T] | tuple[T, ...]

        :return: True if self is less than or equal to `other`.
        :rtype: bool
        """
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) <= tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __ge__(self: AbstractSequence[T], other: AbstractSequence[T] | list[T] | tuple[T, ...]) -> bool:
        """
        Checks if this sequence is greater than or equal to another.

        :param other: Another sequence to compare with.
        :type other: AbstractSequence[T] | list[T] | tuple[T, ...]

        :return: True if self is greater than or equal to `other`.
        :rtype: bool
        """
        if isinstance(other, (AbstractSequence, list, tuple)):
            return tuple(self.values) >= tuple(other.values if isinstance(other, AbstractSequence) else other)
        return NotImplemented

    def __add__(
        self: AbstractSequence[T],
        other: AbstractSequence[T] | list[T] | tuple[T, ...]
    ) -> AbstractSequence[T]:
        """
        Concatenates this sequence with another sequence, list or tuple of compatible types.

        :param other: The sequence or iterable to concatenate.
        :type other: AbstractSequence[T] | list[T] | tuple[T]

        :return: A new AbstractSequence of the same dynamic subclass as self containing the elements from `other` added
        right after the ones from self, as done by the __add__ method of the underlying value container.
        :rtype: AbstractSequence[T]

        :raises TypeError: If `other` has incompatible types.
        """
        from type_validation import _validate_collection_type_and_get_values
        if not isinstance(other, (AbstractSequence, list, tuple)):
            return NotImplemented
        return type(self)(self.values + _validate_collection_type_and_get_values(other, self.item_type))

    def __mul__(
        self: AbstractSequence[T],
        n: int
    ) -> AbstractSequence[T]:
        """
        Repeats this sequence `n` times.

        :param n: Number of times to repeat the sequence.
        :type n: int

        :return: A new AbstractSequence of the same dynamic subclass as self with its elements repeated `n` times.
        :rtype: AbstractSequence[T]

        :raises TypeError: If n is not an integer.
        """
        if not isinstance(n, int):
            return NotImplemented
        return type(self)(self.values * n, _skip_validation=True)

    def __sub__(self: AbstractSequence[T], other: Iterable[T]) -> AbstractSequence[T]:
        """
        Returns a new sequence with the elements of `other` removed.

        :param other: A collection of elements to exclude.
        :type other: Iterable

        :return: A new AbstractSequence of the same dynamic subclass as self with all elements present in `other` removed.
        :rtype: AbstractSequence[T]
        """
        return self.filter(lambda item : item not in other)

    def __reversed__(self: AbstractSequence[T]) -> Iterator[T]:
        """
        Returns a reversed iterator over the sequence.

        :return: A reversed iterator, delegated to the __reversed__ method of the underlying container.
        :rtype: Iterator[T]
        """
        return reversed(self.values)

    def reversed(self) -> AbstractSequence[T]:
        """
        Returns a new sequence with elements in reverse order.

        :return: A new reversed AbstractSequence of the same dynamic subclass as self containing its elements in
        reversed order.
        :rtype: AbstractSequence[T]
        """
        return type(self)(reversed(self.values), _skip_validation=True)

    def index(self: AbstractSequence[T], value: T) -> int:
        """
        Returns the index of the first occurrence of a value.

        :param value: The value to search for.
        :type value: T

        :return: Index of the first appearance of the value.
        :rtype: int

        :raises ValueError: If the value is not found.
        """
        return self.values.index(value)

    def get_index(self: AbstractSequence[T], value: T, fallback: int = -1) -> int:
        """
        Returns the index of the first occurrence of a value, or a fallback if it isn't found.

        :param value: The value to search for.
        :type value: T

        :param fallback: Number to return if the value isn't found. Defaulted to -1.
        :type fallback: int

        :return: Index of the first appearance of the value.
        :rtype: int
        """
        try:
            return self.values.index(value)
        except ValueError:
            return fallback

    def sorted(
        self: AbstractSequence[T],
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False
    ) -> AbstractSequence[T]:
        """
        Returns a new sequence with its elements sorted by an optional key.

        :param key: Optional function to extract comparison key from elements.
        :type key: Callable[[T], Any] | None

        :param reverse: Whether to sort in descending order.
        :type reverse: bool

        :return: A new AbstractSequence of the same dynamic subclass as self with the same elements but sorted
        according to the key and reverse parameters.
        :rtype: AbstractSequence[T]
        """
        return type(self)(sorted(self.values, key=key, reverse=reverse), _skip_validation=True)


@forbid_instantiation
class AbstractMutableSequence[T](AbstractSequence[T]):
    """
    Abstract base class for mutable and ordered sequences containing values of a type T.

    This class extends AbstractSequence by adding mutation capabilities such as appending, inserting, removing, and
    sorting. It is still an abstract class, so it must be subclassed to create concrete implementations.

    It overrides _finisher to list to ensure the mutability of the internal container, and also adds the attribute
    _mutable set to True as class metadata, that for now is unused.
    """

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = list
    _mutable: ClassVar[bool] = True

    def append(
        self: AbstractMutableSequence[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Appends a value to the end of the sequence, delegating on the underlying container's __append__ method.

        :param value: The value to append.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value into the expected type.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_value
        self.values.append(_validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def __setitem__(
        self: AbstractMutableSequence[T],
        index: int | slice,
        value: T | AbstractSequence[T] | list[T] | tuple[T],
        *,
        _coerce: bool = False
    ) -> None:
        """
        Replaces an item or slice in the sequence with new value(s), delegating on the underlying container's __setitem__.

        :param index: Index or slice to replace.
        :type index: int | slice

        :param value: Value(s) to assign.
        :type value: T | AbstractSequence[T] | list[T] | tuple[T]

        :param _coerce: State parameter that, if True, attempts to coerce the value(s) into the expected type.
        :type _coerce: bool

        :raises TypeError: If index is not int or slice.
        """
        from type_validation import _validate_collection_type_and_get_values, _validate_or_coerce_value

        if isinstance(index, slice):
            self.values[index] = _validate_collection_type_and_get_values(value, self.item_type)

        elif isinstance(index, int):
            self.values[index] = _validate_or_coerce_value(value, self.item_type, _coerce=_coerce)

        else:
            raise TypeError("Invalid index type: must be int or slice")

    def __delitem__(self: AbstractMutableSequence[T], index: int | slice) -> None:
        """
        Deletes an item or slice from the sequence delegating on the underlying container's __delitem__.

        :param index: Index or slice to delete.
        :type index: int | slice
        """
        del self.values[index]

    def __iadd__(
        self: AbstractMutableSequence[T],
        other: AbstractSequence[T] | list[T] | tuple[T, ...]
    ) -> AbstractMutableSequence[T]:
        """
        Appends the elements from `other` to this sequence in-place.

        This method modifies `self.values` directly by extending it with the validated elements from `other`.

        :param other: The sequence or iterable whose elements will be appended.
        :type other: AbstractSequence[T] | list[T] | tuple[T]

        :return: Self after appending the contents of `other`.
        :rtype: AbstractMutableSequence[T]

        :raises TypeError: If `other` contains elements of an incompatible type.
        """
        from type_validation import _validate_collection_type_and_get_values
        if not isinstance(other, (AbstractSequence, list, tuple)):
            return NotImplemented
        self.extend(other)
        return self

    def __imul__(self: AbstractMutableSequence[T], n: int) -> AbstractMutableSequence[T]:
        """
        Repeats the contents of this sequence `n` times in-place.

        :param n: The number of times to repeat the sequence.
        :type n: int

        :return: Self after repetition.
        :rtype: AbstractMutableSequence[T]

        :raises TypeError: If `n` is not an integer.
        """
        if not isinstance(n, int):
            return NotImplemented
        self.values[:] = self.values * n
        return self

    def __isub__(self: AbstractMutableSequence[T], other: Iterable[T]) -> AbstractMutableSequence[T]:
        """
        Removes all elements in `other` from this sequence in-place.

        Retains only elements that are not in `other`, preserving order.

        :param other: An iterable of elements to remove.
        :type other: Iterable[T]

        :return: Self after removing all matching elements.
        :rtype: AbstractMutableSequence[T]
        """
        self.values[:] = [item for item in self.values if item not in other]
        return self

    def sort(
        self: AbstractMutableSequence[T],
        key: Callable[[T], Any] | None = None,
        reverse: bool = False
    ) -> None:
        """
        Sorts the sequence in place according to an optional key.

        :param key: Optional function to extract comparison key from elements.
        :type key: Callable[[T], Any] | None

        :param reverse: State parameter that, if True, sorts in descending order.
        :type reverse: bool
        """
        self.values.sort(key=key, reverse=reverse)

    def insert(
        self: AbstractMutableSequence[T],
        index: int,
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Inserts a value at the specified index delegating on the underlying container's insert method.

        :param index: The index at which to insert.
        :type index: int

        :param value: The value to insert.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value into the expected type.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_value
        self.values.insert(index, _validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def extend(self, other: Iterable[T], *, _coerce: bool = False) -> None:
        """
        Extends the sequence with elements from another iterable.

        :param other: The iterable whose elements to add.
        :type other: Iterable[T]

        :param _coerce: If True, attempts to coerce each value into the expected type.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_iterable
        self.values.extend(_validate_or_coerce_iterable(other, self.item_type, _coerce=_coerce))

    def pop(self, index: int = -1) -> T:
        """
        Removes and returns the item at the given position (default at the last position).

        :param index: Index of the element to remove. Defaults to -1 (last element).
        :type index: int

        :return: The removed element, as returned by the underlying container's pop method.
        :rtype: T
        """
        return self.values.pop(index)

    def remove(
        self: AbstractSequence[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Removes the first occurrence of a value from the sequence.

        :param value: The value to remove.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value before removing it.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_value
        value_to_remove = value
        if _coerce:
            try:
                value_to_remove = _validate_or_coerce_value(value, self.item_type)
            except (TypeError, ValueError):
                pass
        self.values.remove(value_to_remove)


@forbid_instantiation
class AbstractSet[T](Collection[T]):
    """
    Abstract base class for hashable Collections of type T supporting set operations.

    This class extends Collection, providing standard set-theoretic operations (union, intersection, difference,
    symmetric difference) and comparison methods specifically tailored to sets. It is still an abstract class, so it
    must be subclassed to create concrete implementations.

    It overrides _finisher to frozenset to ensure the immutability and set properties of the underlying container.

    This class will be further extended by AbstractMutableSet, adding mutability capabilities to it.
    """

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = frozenset

    def __eq__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether two AbstractSet instances are equal in both type and contents.

        :param other: The object to compare with.
        :type other: Any

        :return: True if both sets contain the same items and item type, False otherwise.
        :rtype: bool
        """

        return (
            isinstance(other, AbstractSet)
            and self.item_type == other.item_type
            and set(self.values) == set(other.values)
        )

    def __lt__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a proper subset of another AbstractSet.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a proper subset of `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values < other.values
        return NotImplemented

    def __le__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a subset (or equal to) another AbstractSet.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a subset or equal to `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values <= other.values
        return NotImplemented

    def __gt__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a proper superset of another AbstractSet.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a proper superset of `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values > other.values
        return NotImplemented

    def __ge__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a superset (or equal to) another AbstractSet.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a superset or equal to `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values >= other.values
        return NotImplemented

    def __or__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the union of two AbstractSet instances.

        :param other: The set to union with.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements from both sets.
        :rtype: AbstractSet[T]
        """
        return type(self)(self.values | other.values)

    def __and__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the intersection of two AbstractSet instances.

        :param other: The set to intersect with.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements present in both sets.
        :rtype: AbstractSet[T]
        """
        return type(self)(self.values & other.values)

    def __sub__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the difference between two AbstractSet instances.

        :param other: The set whose elements to subtract.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements of self not present
        in `other`.
        :rtype: AbstractSet[T]
        """
        return type(self)(self.values - other.values)

    def __xor__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the symmetric difference between two AbstractSet instances.

        :param other: The set to symmetric-difference with.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements in either set but not both.
        :rtype: AbstractSet[T]
        """
        return type(self)(self.values ^ other.values)

    def union(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        """
        Returns the union of this set with one or more iterables or collections.

        The operation is delegated to the underlying container's union method, which should support passing multiple
        iterable arguments.

        :param others: One or more iterables or collections to union with.
        :type others: Iterable[T] | Collection[T]

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing all distinct elements of self and
        all the iterables passed.
        :rtype: AbstractSet[T]
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.union(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)))

    def intersection(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        """
        Returns the intersection of this set with one or more iterables or collections.

        The operation is delegated to the underlying container's union method, which should support passing multiple
        iterable arguments.

        :param others: One or more iterables or collections to intersect with.
        :type others: Iterable[T] | Collection[T]

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing the elements common to self and all
        passed iterables.
        :rtype: AbstractSet[T]
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.intersection(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)))

    def difference(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        """
        Returns the difference between this set and one or more iterables or collections.

        The operation is delegated to the underlying container's union method, which should support passing multiple
        iterable arguments.

        :param others: One or more iterables or collections to subtract.
        :type others: Iterable[T] | Collection[T]

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing its elements that are not present in
        any of the others.
        :rtype: AbstractSet[T]
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.difference(*_validate_or_coerce_iterable_of_iterables(others, self.item_type,_coerce=_coerce)))

    def symmetric_difference(
        self: AbstractSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> AbstractSet[T]:
        """
        Returns the symmetric difference between this set and one or more iterables or collections.

        :param others: One or more iterables or collections to compare.
        :type others: Iterable[T] | Collection[T]

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing the elements that are present in only
        one of self or the passed iterables.
        :rtype: AbstractSet[T]
        """
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
        """
        Checks if this set is a subset of another set or AbstractSet.

        :param other: The set to compare against.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :param _coerce: State parameter that, if True, attempts to coerce values before checking.
        :type _coerce: bool

        :return: True if this set is a subset of `other`, False otherwise.
        :rtype: bool
        """
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
        """
        Checks if this set is a superset of another set or AbstractSet.

        :param other: The set to compare against.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :param _coerce: State parameter that, if True, attempts to coerce values before checking.
        :type _coerce: bool

        :return: True if this set is a superset of `other`, False otherwise.
        :rtype: bool
        """
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
        """
        Checks if this set is disjoint with another set or AbstractSet.

        :param other: The set to compare against.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :param _coerce: State parameter that, if True, attempts to coerce values before checking.
        :type _coerce: bool

        :return: True if this set has no elements in common with `other`, False otherwise.
        :rtype: bool
        """
        from type_validation import _validate_collection_type_and_get_values
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.isdisjoint(_validate_collection_type_and_get_values(other, self.item_type, _coerce=_coerce))


@forbid_instantiation
class AbstractMutableSet[T](AbstractSet[T]):
    """
    Abstract base class for mutable, hashable Collections of type T.

    This class extends AbstractSet and adds methods capable of mutating its underlying internal container, such as
    various updates and in-place operations. It is still an abstract class, so it must be subclassed to create concrete
    implementations.

    It overrides _finisher to set to ensure the mutability of the internal container, and also adds the attribute
    _mutable set to True as class metadata, that for now is unused.
    """

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = set
    _mutable: ClassVar[bool] = True

    def __ior__(self: AbstractMutableSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> AbstractMutableSet[T]:
        """
        In-place union update with another AbstractSet with the operator |=.

        :param other: The set to union with.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :return: This updated AbstractMutableSet.
        :rtype: AbstractMutableSet[T]
        """
        from type_validation import _validate_or_coerce_iterable
        self.update(other)
        return self

    def __iand__(self: AbstractMutableSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> AbstractMutableSet[T]:
        """
        In-place intersection update with another AbstractSet with the operator &=.

        :param other: The set to intersect with.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :return: This updated AbstractMutableSet.
        :rtype: AbstractMutableSet[T]
        """
        from type_validation import _validate_or_coerce_iterable
        self.intersection_update(other)
        return self

    def __isub__(self: AbstractMutableSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> AbstractMutableSet[T]:
        """
        In-place difference update with another AbstractSet with the operator -=.

        :param other: The set whose elements should be removed from this set.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :return: This updated AbstractMutableSet.
        :rtype: AbstractMutableSet[T]
        """
        from type_validation import _validate_or_coerce_iterable
        self.difference_update(other)
        return self

    def __ixor__(self: AbstractMutableSet[T], other: AbstractSet[T] | set[T] | frozenset[T]) -> AbstractMutableSet[T]:
        """
        In-place symmetric difference update with another AbstractSet with the operator ^=.

        :param other: The set whose elements should be removed from this set.
        :type other: AbstractSet[T] | set[T] | frozenset[T]

        :return: This updated AbstractMutableSet.
        :rtype: AbstractMutableSet[T]
        """
        from type_validation import _validate_or_coerce_iterable
        self.symmetric_difference_update(other)
        return self

    def add(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Add a single element to the set.

        Delegates the operation to the underlying container's add method.

        :param value: The element to add.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value to the expected item type.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_value
        self.values.add(_validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def remove(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Remove a single element from the set, or raises a KeyError if not present.

        Delegates the operation to the underlying container's remove method.

        :param value: The element to remove.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value before removal.
        :type _coerce: bool

        :raise KeyError: If the element is not present.
        """
        from type_validation import _validate_or_coerce_value
        value_to_remove = value
        if _coerce:
            try:
                value_to_remove = _validate_or_coerce_value(value, self.item_type)
            except (TypeError, ValueError):
                pass
        self.values.remove(value_to_remove)

    def discard(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Discard an element from the set if present. No error is raised if the element is absent.

        Delegates the operation to the underlying container's discard method.

        :param value: The element to discard.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value before discarding.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_value
        value_to_remove = value
        if _coerce:
            try:
                value_to_remove = _validate_or_coerce_value(value, self.item_type)
            except (TypeError, ValueError):
                pass
        self.values.discard(value_to_remove)

    def clear(self: AbstractMutableSet[T]) -> None:
        """
        Remove all elements from the set.
        """
        self.values.clear()

    def pop(self: AbstractMutableSet[T]) -> T:
        """
        Remove and return an arbitrary element from the set.

        Delegates the operation to the underlying container's pop method.

        :return: The element that was removed.
        :rtype: T
        """
        return self.values.pop()

    def update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        """
        Update the set with elements from one or more iterables or Collections.

        :param others: One or more iterables or Collections whose elements will be added to this set.
        :type others: Iterable[T] | Collection[T]
        :param _coerce: State parameter that, if True, attempts to coerce all elements to the expected type.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def difference_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        """
        Remove all elements found in one or more provided collections.

        :param others: One or more iterables or Collections whose elements will be removed from this set.
        :type others: Iterable[T] | Collection[T]
        :param _coerce: State parameter that, if True, attempts to coerce all elements before removal.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.difference_update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def intersection_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        """
        Retain only elements that are also in all provided collections.

        :param others: One or more iterables or Collections to intersect and update with.
        :type others: Iterable[T] | Collection[T]
        :param _coerce: State parameter that, if True, attempts to coerce all elements before intersection.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.intersection_update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def symmetric_difference_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T] | Collection[T],
        _coerce: bool = False
    ) -> None:
        """
        Update the set to contain elements that are in exactly one of the sets.

        :param others: One or more iterables or Collections to symmetrically differ with.
        :type others: Iterable[T] | Collection[T]
        :param _coerce: State parameter that, if True, attempts to coerce all elements before processing.
        :type _coerce: bool
        """
        from type_validation import _validate_or_coerce_iterable_of_iterables
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            self.values.symmetric_difference_update(validated_set)


@forbid_instantiation
class AbstractDict[K, V](GenericBase[K, V]):
    """
    Abstract base class representing a dictionary with type enforced keys and values given by generic types.

    Provides a base class for storing and operating on dictionaries with keys and values of a common type each. It uses
    generics to enforce runtime type safety and supports fluent and functional-style operations inspired by Java's
    Stream API.

    The class enforces runtime generic type tracking using a metaclass extension (GenericBase), allowing validation
    and coercion of elements during construction and transformations. It cannot be directly instantiated and must be
    parameterized by two concrete types when the constructor is called (e.g., MutableDict[int, str]).

    Attributes:
        key_type (type[K]): The type constraint for keys.
        value_type (type[V]): The type constraint for values.
        data (dict[K, V]): The underlying dictionary storage.

    Note:
        Any method that returns a new AbstractDict instance (e.g., filter, map, etc.) constructs the returned
        value using type(self)(...). This ensures that:

            - The returned object has the same concrete runtime subclass as self.
            - Generic type parameters (K, V) are preserved without reapplying __class_getitem__, because they are
              already bound via the dynamic subclassing mechanism in __class_getitem__.

        This makes behavior consistent across all subclasses of AbstractDict: type(self) guarantees the returned value
        matches the exact type and structure of self, unless otherwise explicitly overridden. Also, calling
        type(self)[new_key_type, new_value_type] correctly creates a new dynamic subclass with the same base class as
        self but with the new generic types.
    """

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    _finisher: ClassVar[Callable[[dict], Any]] = immutabledict

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
        """
        Initialize an AbstractDict with type validation and optional coercion.

        :param keys_values: A dict, mapping, iterable of (key, value) tuples, or another AbstractDict.
        :type keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None

        :param _keys: Optional keys iterable used in conjunction with `_values`.
        :type _keys: Iterable[K] | None

        :param _values: Optional values iterable used in conjunction with `_keys`.
        :type _values: Iterable[V] | None

        :param _coerce_keys: Whether to coerce keys to the declared type.
        :type _coerce_keys: bool

        :param _coerce_values: Whether to coerce values to the declared type.
        :type _coerce_values: bool

        :param _finisher: Callable applied to the final dict (defaults to identity).
        :type _finisher: Callable[[dict[K, V]], Any]

        :param _skip_validation: If True, skips all type validation and coercion.
        :type _skip_validation: bool
        """
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
        """
        Returns the inferred key and value types for this class if they were provided.

        This method inspects the generic arguments applied to the class, stored in its _args attribute inherited from
        GenericBase and returns them. It returns (None, None) if the types are not yet specified.

        :return: Tuple of (key_type, value_type) or (None, None) if not inferred.
        :rtype: tuple[type[K] | None, type[V] | None]
        """
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
        """
        Infer key/value types from the input and construct an AbstractDict containing them.

        :param keys_values: The data to infer types from and use to initialize the dictionary.
        :type keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]

        :return: A new AbstractDict with inferred generic types and properly validated contents (hashable and not
        duplicated keys).
        :rtype: AbstractDict[K, V]
        """
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
        """
        Constructs an AbstractDict from separate keys and values iterables, inferring their types.

        :param keys: An iterable of keys.
        :type keys: Iterable[K]

        :param values: An iterable of values, matching the length of `keys`.
        :type values: Iterable[V]

        :return: A new AbstractDict initialized from the given key-value pairs.
        :rtype: AbstractDict[K, V]

        :raises ValueError: If `keys` and `values` do not have the same length.
        """
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
        Returns a value for a given key, or a sliced subdictionary for a slice of keys.

        - If a single key is passed, returns its associated value.
        - If a `slice` is passed (e.g., `dict[start:stop]`), returns a new `AbstractDict[K, V]`
          with all keys within that range. Step is not supported.

        :param key: A key of type K or a slice over the key space.
        :type key: K | slice

        :return: The value associated with the key, or a sliced subdictionary.
        :rtype: V | AbstractDict[K, V]

        :raises TypeError: If the keys are not orderable for slicing or if the slice step is not None.
        :raises KeyError: If the key is not found.
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

    def __iter__(self: AbstractDict[K, V]) -> Iterator[K]:
        """
        Returns an iterator over the keys of this AbstractDict.

        :return: An iterator over all keys.
        :rtype: Iterator[K]
        """
        return iter(self.data)

    def keys(self: AbstractDict[K, V]):
        """
        Returns a view of the dictionary's keys.
        :rtype: dict_keys[K]
        """
        return self.data.keys()

    def values(self: AbstractDict[K, V]):
        """
        Returns a view of the dictionary's values.
        :rtype: dict_values[V]
        """
        return self.data.values()

    def items(self: AbstractDict[K, V]):
        """
        Returns a view of the dictionary's key-value pairs.
        :rtype: dict_items[K, V]
        """
        return self.data.items()

    def __len__(self: AbstractDict[K, V]) -> int:
        """
        Returns the number of items in this AbstractDict.

        :return: The number of key-value pairs present.
        :rtype: int
        """
        return len(self.data)

    def __contains__(self: AbstractDict[K, V], key: Any) -> bool:
        """
        Checks whether the given key is present on the AbstractDict.

        :param key: The key to check.
        :type key: Any

        :return: True if the key exists, False otherwise.
        :rtype: bool
        """
        return key in self.data

    def __eq__(self: AbstractDict[K, V], other: Any) -> bool:
        """
        Checks equality with another AbstractDict.

        Two dictionaries are considered equal if they share the same class, key/value types, and contents.

        :param other: The object to compare against.
        :type other: Any

        :return: True if `other` is an AbstractDict with the same key and values types and contents, False otherwise.
        :rtype: bool
        """
        return (
            isinstance(other, AbstractDict)
            and self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def __repr__(self: AbstractDict[K, V]) -> str:
        """
        Returns a concise string representation of this AbstractDict, including its generic types for keys and values.

        :return: A string representation of this AbstractDict.
        :rtype: str
        """

        return f"{class_name(type(self))}{dict(self.data)}"

    def __or__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns the union of this AbstractDict and another mapping.

        :param other: The other mapping to merge.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self containing all key-value pairs from both, with
        `other` overriding duplicate keys.
        :rtype: AbstractDict[K, V]
        """
        return type(self)(dict(self.data) | dict(other))

    def __and__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns the intersection of this AbstractDict with another mapping.

        :param other: The other mapping.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self with only keys present in both mappings.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({k: self.data[k] for k in self.data.keys() & other.keys()})

    def __sub__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns a new dictionary with the keys that are not in `other`.

        :param other: The mapping to subtract from this one.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self without the keys found in `other`.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({k: v for k, v in self.data.items() if k not in other})

    def __xor__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns the symmetric difference between this AbstractDict and another mapping.

        :param other: The other mapping.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self containing keys only in one of the two mappings.
        :rtype: AbstractDict[K, V]
        """
        sym_keys = self.data.keys() ^ other.keys()
        return type(self)({k: (self.data.get(k) or other.get(k)) for k in sym_keys})

    def to_dict(self: AbstractDict[K, V]) -> dict[K, V]:
        """
        Returns a shallow copy of the underlying data dictionary as a Python dict.

        :return: A native Python dictionary with the same contents.
        :rtype: dict[K, V]
        """
        return dict(self.data)

    def to_immutable_dict(self: AbstractDict[K, V]) -> immutabledict[K, V]:
        """
        Returns an immutabledict representation of the AbstractDict.

        :return: A frozen version of the current dictionary.
        :rtype: immutabledict[K, V]
        """
        return immutabledict(self.data)

    def copy(self: AbstractDict[K, V], deep: bool = False) -> AbstractDict[K, V]:
        """
        Returns a shallow or deep copy of the AbstractDict.

        If the underlying data dictionary implements `.copy()`, it uses that method for shallow copies. For deep copies,
        it uses `deepcopy` to recursively duplicate all contents. Skips re-validation for performance.

        The result is of the same dynamic subclass as `self`, with identical key and value types.

        :param deep: Boolean state parameter to control if the copy is shallow or deep.
        :type deep: bool

        :return: A shallow or deep copy of the object.
        :rtype: AbstractDict[K, V]
        """
        from copy import deepcopy
        data = deepcopy(self.data) if deep else (self.data.copy() if hasattr(self.data, 'copy') else self.data)
        return type(self)(data, _skip_validation=True)

    def get(
        self: AbstractDict[K, V],
        key: K,
        fallback: V | None = None,
        *,
        _coerce_keys: bool = False,
        _coerce_values: bool = False
    ) -> V | None:
        """
        Returns the value for a given key if present, else returns a fallback (after optional coercion).

        :param key: The key to search for.
        :type key: K

        :param fallback: The fallback value if the key is missing.
        :type fallback: V | None

        :param _coerce_keys: Whether to coerce the input key to the key type.
        :type _coerce_keys: bool

        :param _coerce_values: Whether to coerce the fallback value if returned.
        :type _coerce_values: bool

        :return: The value assigned to the key in the dictionary, or the fallback.
        :rtype: V | None
        """
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
        """
        Applies a function to all values and returns a new AbstractDict with the updated values.

        The key type is preserved, and the resulting value type can either be inferred or provided manually.
        The output dictionary is of the same subclass as self.

        :param f: A function mapping each value to a new value.
        :type f: Callable[[V], R]

        :param result_type: Optional explicit result type for values after transformation.
        :type result_type: type[R] | None

        :param _coerce_values: State parameter that, if True, coerces the transformed values to the given result type.
        :type _coerce_values: bool

        :return: A new AbstractDict of the same subclass as self with transformed values. Its key type is the same as
        self, and its value type is either inferred from the mapped values or taken from result_type if it's not None.
        :rtype: AbstractDict[K, R]
        """
        new_data = {key : f(value) for key, value in self.data.items()}
        if result_type is not None:
            return type(self)[self.key_type, result_type](new_data, _coerce_values=_coerce_values)
        else:
            from type_validation import _infer_type_contained_in_iterable
            inferred_return_type = _infer_type_contained_in_iterable(new_data.values())
            return type(self)[self.key_type, inferred_return_type](new_data, _skip_validation=True)

    def filter_keys(self: AbstractDict[K, V], predicate: Callable[[K], bool]) -> AbstractDict[K, V]:
        """
        Returns a new AbstractDict containing only the (key, value) pairs whose keys satisfy a predicate.

        :param predicate: A function to the booleans that returns True for keys to retain.
        :type predicate: Callable[[K], bool]

        :return: A new AbstractDict of the same dynamic subclass as self containing the filtered (key, value) pairs.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({key : value for key, value in self.data.items() if predicate(key)})

    def filter_values(self: AbstractDict[K, V], predicate: Callable[[V], bool]) -> AbstractDict[K, V]:
        """
        Returns a new AbstractDict containing only the (key, value) pairs whose values satisfy a predicate.

        :param predicate: A function to the booleans that returns True for values to retain.
        :type predicate: Callable[[V], bool]

        :return: A new AbstractDict of the same dynamic subclass as self containing the filtered (key, value) pairs.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({key : value for key, value in self.data.items() if predicate(value)})

    def filter_items(self: AbstractDict[K, V], predicate: Callable[[K, V], bool]) -> AbstractDict[K, V]:
        """
        Returns a new AbstractDict containing only the (key, value) pairs that satisfy a (key, value) predicate.

        :param predicate: A function that returns True for pairs to retain.
        :type predicate: Callable[[K, V], bool]

        :return: A new AbstractDict of the same dynamic subclass as self containing the filtered key-value pairs.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({key : value for key, value in self.data.items() if predicate(key, value)})


@forbid_instantiation
class AbstractMutableDict[K, V](AbstractDict[K, V]):
    """
    Abstract base class for mutable dictionaries with type enforced keys and values.

    Inherits from AbstractDict, extending it with mutation operations such as item assignment, deletion, and updates.
    It is still an abstract class, so it must be subclassed to create concrete implementations.

    It overrides _finisher to dict to ensure the mutability of the internal container, and also adds the attribute
    _mutable set to True as class metadata, that for now is unused.
    """

    _finisher: ClassVar[Callable[[dict], Mapping]] = dict
    _mutable: bool = True

    def __setitem__(self: AbstractMutableDict[K, V], key: K, value: V) -> None:
        """
        Inserts or updates a key-value pair in this AbstractMutableDict.

        Both the key and value are validated against their expected types.

        :param key: The key to insert or update.
        :type key: K

        :param value: The value to associate with the key.
        :type value: V
        """
        from type_validation import _validate_or_coerce_value
        self.data[_validate_or_coerce_value(key, self.key_type)] = _validate_or_coerce_value(value, self.value_type)

    def __delitem__(self: AbstractMutableDict[K, V], key: K) -> None:
        """
        Deletes a key-value pair from this AbstractMutableDict by key.

        :param key: The key to remove.
        :type key: K
        :raises KeyError: If the key does not exist.
        """
        del self.data[key]

    def clear(self: AbstractMutableDict[K, V]) -> None:
        """
        Removes all key-value pairs from this AbstractMutableDict.
        """
        self.data.clear()

    def __ior__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place union update with another mapping.

        Equivalent to calling `.update()` with the given mapping. Values from `other` override any existing values.

        :param other: A mapping containing the new key-value pairs to update.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        self.update(other)
        return self

    def __iand__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place intersection with another mapping by removing keys not present in `other`.

        :param other: The mapping to intersect keys with.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        keys_to_remove = set(self.data) - set(other)
        for key in keys_to_remove:
            del self.data[key]
        return self

    def __isub__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place difference by removing keys found in `other`.

        :param other: The mapping whose keys will be removed.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        for key in other:
            self.data.pop(key, None)
        return self

    def __ixor__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place symmetric difference update with another mapping, keeping only the keys found in one but not both.

        :param other: The mapping to symmetrically differentiate with.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
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
        """
        Updates this AbstractMutableDict with the contents of another mapping.

        Values from `other` override existing values for their keys.

        :param other: The mapping to merge into this AbstractMutableDict.
        :type other: dict[K, V] | Mapping[K, V] | AbstractDict[K, V]

        :param _coerce_keys: State parameter that, if True, attempts to coerce keys before validation.
        :type _coerce_keys: bool

        :param _coerce_values: State parameter that, if True, attempts to coerce values before validation.
        :type _coerce_values: bool
        """
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
        """
        Removes and returns the value associated with a key, or a fallback if not found.

        :param key: The key to remove.
        :type key: K

        :param fallback: Optional fallback value if key is not present.
        :type fallback: V | None

        :param _coerce_keys: State parameter that, if True, attempts to coerce the key before popping.
        :type _coerce_keys: bool | None

        :param _coerce_values: State parameter that, if True, attempts to coerce the fallback before returning it.
        :type _coerce_values: bool | None

        :return: The value associated with the removed key or the fallback.
        :rtype: V
        """
        from type_validation import _validate_or_coerce_value
        if fallback is not None:
            return self.data.pop(
                _validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys),
                _validate_or_coerce_value(fallback, self.value_type, _coerce=_coerce_values)
            )
        return self.data.pop(_validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys))

    def popitem(self: AbstractMutableDict[K, V]) -> tuple[K, V]:
        """
        Removes and returns the last inserted key-value pair.

        :return: A tuple of the removed key and value.
        :rtype: tuple[K, V]
        """
        return self.data.popitem()

    def setdefault(self: AbstractMutableDict[K, V], key: K, default: V | None = None) -> V:
        """
        Returns the value for a key, inserting a default value if the key is not present.

        :param key: The key to look up or insert.
        :type key: K

        :param default: The value to insert if the key is not present.
        :type default: V

        :return: The existing or newly inserted value.
        :rtype: V
        """
        from type_validation import _validate_or_coerce_value
        if default is None:
            return self.data.setdefault(_validate_or_coerce_value(key, self.key_type))
        return self.data.setdefault(
            _validate_or_coerce_value(key, self.key_type),
            _validate_or_coerce_value(default, self.value_type)
        )
