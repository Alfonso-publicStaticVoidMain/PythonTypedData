from __future__ import annotations

from functools import reduce
from typing import Iterable, Any, Callable, TypeVar, ClassVar, Iterator
from collections import defaultdict

from abstract_classes.generic_base import GenericBase, class_name, forbid_instantiation


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
        item_type (type[T]): The type of elements stored in the collection, derived from the generic type.

        values (Any): The internal container of stored values, usually of one of Python's built-in Iterables.

        _finisher (ClassVar[Callable]): A function that is applied to the values during __init__ before setting it as the
        attribute of the object. It's generally used to transform them into another Iterable type. If missing, it's
        assumed to be the identity mapping on Collection's __init__ method.

    Note:
        Any method that returns a new Collection instance (e.g., filter, union, sorted, etc.) constructs the returned
        value using type(self)(...). This is because:
            - In order for the `self` object to have been created in the first place, its Collection subclass must have
              called __class_getitem__ in order to acquire a generic type, otherwise Collection's __init__ would have
              thrown an error.
            - In that call to __class_getitem__, the generic type it was called upon was stored in the _args attribute
              of the class it returned, which is precisely type(self), while the original Collection subclass was stored
              in the _origin attribute.
            - Then, calling type(self)'s constructor correctly passes to Collection's __init__ the same values of the
              generic types that were used to construct `self`, as well as the same base subclass, ensuring then they have
              the same structure.
            - Furthermore, calling type(self)[another_item_type] correctly creates a new dynamic subclass with the same
              base class as self but with the new generic type.
        This makes behavior consistent across all subclasses of Collection: type(self) guarantees the returned value
        matches the exact type and structure of self, unless otherwise explicitly overridden.
    """

    item_type: type[T]
    values: Any

    def __init__(
        self: Collection[T],
        *values: T,
        _coerce: bool = False,
        _forbidden_iterable_types: tuple[type, ...] | None = None,
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
        from type_validation.type_validation import _validate_or_coerce_iterable, _validate_type

        # The generic type of the Collection is fetched from its _args attribute inherited from GenericBase.
        generic_item_type: type = type(self)._inferred_item_type()

        # If the generic item type is None or a TypeVar, raises a TypeError.
        if generic_item_type is None:
            raise TypeError(f"{type(self).__name__} must be instantiated with a generic type, e.g., MutableList[int](...) or via .of().")

        if isinstance(generic_item_type, TypeVar):
            raise TypeError(f"{type(self).__name__} was instantiated without a generic type, somehow {generic_item_type} was a TypeVar.")

        if (
            len(values) == 1  # The values are of length 1.
            and not _validate_type(values[0], generic_item_type)  # Their only value doesn't validate the expected type.
            and isinstance(values[0], Iterable)  # Their only value is an Iterable.
            and not isinstance(values[0], (str, bytes))  # But it's not a str or bytes.
        ):
            values = values[0]  # Then, the values are unpacked.

        _forbidden_iterable_types = _forbidden_iterable_types or getattr(type(self), '_forbidden_iterable_types', ())

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

        Acts as a type-safe factory method for constructing properly parameterized collections when the type
        is not known beforehand.

        :param values: One or more parameters, or an Iterable of values to initialize the new Collection with.
        :type values: T

        :return: A new Collection that is an instance of cls containing the passed values, inferring its item_type from
        _infer_type_contained_in_iterable method.
        :rtype: Collection[T]

        :raises ValueError: If no values are provided.
        """
        if len(values) == 1 and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            values = tuple(values[0])
        from type_validation.type_validation import _infer_type_contained_in_iterable
        return cls[_infer_type_contained_in_iterable(values)](values, _skip_validation=True)

    @classmethod
    def empty[R](cls: type[Collection[R]]) -> Collection[R]:
        """
        Creates an empty Collection subclass of the current class, parameterized with its generic type.

        Useful for initialization of empty collections with known type context.

        :return: An empty Collection that is an instance of cls with the given item_type.
        :rtype: Collection[R]

        :raises ValueError: If item_type is None.
        """
        if cls._inferred_item_type() is None:
            raise ValueError(f"Trying to call {cls.__name__}.empty without a generic type.")
        return cls()

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
class MutableCollection[T](Collection[T]):

    def remove(
        self: MutableCollection[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Removes the first occurrence of a value from the collection.

        :param value: The value to remove.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value before removing it.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_value
        value_to_remove = value
        if _coerce:
            try:
                value_to_remove = _validate_or_coerce_value(value, self.item_type)
            except (TypeError, ValueError):
                pass
        self.values.remove(value_to_remove)

    def clear(self: MutableCollection[T]) -> None:
        """
        Remove all elements from the collection.
        """
        self.values.clear()

    def filter_inplace(self, predicate: Callable[[T], bool]) -> None:
        values_to_remove: list[T] = [v for v in self.values if not predicate(v)]
        for v in values_to_remove:
            try:
                self.values.remove(v)
            except (TypeError, ValueError, KeyError):
                pass

    def map_inplace(
        self: MutableCollection[T],
        f: Callable[[T], T],
        *,
        _coerce: bool = False
    ) -> None:
        replace_many = getattr(self, "replace_many", None)
        if callable(replace_many):
            replace_many({x : f(x) for x in self.values}, _coerce=_coerce)
        else:
            pass

    def remove_all(self, items: Iterable[T]) -> None:
        self.filter_inplace(lambda x: x not in items)

    def retain_all(self, items: Iterable[T]) -> None:
        self.filter_inplace(lambda x: x in items)