from __future__ import annotations

from functools import reduce
from typing import Iterable, Any, Callable, TypeVar, Iterator, Sized
from collections import defaultdict

from abstract_classes.protocols import CollectionProtocol, MutableCollectionProtocol
from abstract_classes.generic_base import GenericBase, class_name, forbid_instantiation, _convert_to

_MISSING = object()


@forbid_instantiation
class Collection[T](GenericBase):
    """
    Abstract base class representing a collection of items of type T, wrapping an underlying container and an item type.

    Provides a base class for storing and operating on collections of items with a common type, without assuming any
    further structure, which will be added on certain extensions like AbstractSequence and AbstractSet. It supports
    functional-style operations inspired by Java's Stream API.

    The class enforces runtime generic type tracking using the metaclass extension GenericBase, from which it inherits
    its __class_getitem__ method, which stores the generic types the Collection subclasses are called upon on an _args
    attribute, and that base subclass as an _origin attribute of a new dynamic subclass, which can then be used to
    instantiate new objects, or perform type validation with full access to the generic types.

    It is an abstract class and cannot be directly instantiated. Its subclasses must be parameterized by a concrete type
    when the constructor is called (e.g., MutableList[int]).

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
              generic types that were used to construct `self`, as well as the same base subclass, ensuring then they
              have the same structure.
        This makes behavior consistent across all subclasses of Collection: type(self)(...) guarantees the returned
        value matches the exact type and structure of self, unless otherwise explicitly overridden.

    Attributes:
        item_type (type[T]): The type of elements stored in the collection, derived from the generic type.

        values (CollectionProtocol[T]): The internal container of stored values, usually of one of Python's
         built-in Iterables. It's expected that it implements __len__, __contains__ and __iter__.
    """

    item_type: type[T]
    values: CollectionProtocol[T]

    def __init__(
        self: Collection[T],
        *values: T | Iterable[T],
        _coerce: bool = False,
        _forbidden_iterable_types: tuple[type, ...] = (),
        _finisher: Callable[[Iterable[T]], CollectionProtocol[T]] = None,
        _skip_validation: bool = False
    ) -> None:
        """
        Basic constructor for the Collection abstract class, to be invoked by all subclasses.

        The attribute item_type is inferred from the generic the class was called upon, which was stored on the
        _args attribute of the class returned by __class_getitem__ and then fetched by _inferred_item_type.

        :param values: Values to store in the Collection, received as an iterable or one by one.
        :type values: T | Iterable[T]

        :param _coerce: State parameter to force type coercion or not. Some numeric type coercions are always performed.
        :type _coerce: bool

        :param _forbidden_iterable_types: Tuple of types that the values parameter cannot be.
        :type _forbidden_iterable_types: tuple[type, ...]

        :param _finisher: Callable to be applied to the values before storing them on the values attribute of the object.
         Defaults to None, and in that case is later assigned to the identity mapping.
        :type _finisher: Callable[[Iterable[T]], collections.abc.Collection[T]]

        :param _skip_validation: State parameter to skip type validation of the values. Only use it in cases where it's
         known that the values received will match the generic type.
        :type _skip_validation: bool

        :raises TypeError: If the generic type wasn't provided or was a TypeVar, or if the values iterable parameter is
         of one of the forbidden iterable types.
        """
        from type_validation.type_validation import _validate_or_coerce_iterable, _validate_type

        # The generic type of the Collection is fetched from its _args attribute inherited from GenericBase.
        generic_item_type: type = type(self)._inferred_item_type()

        # If the generic item type is None or a TypeVar, raises a TypeError.
        if generic_item_type is None:
            raise TypeError(f"{class_name(type(self))} must be instantiated with a generic type, e.g., {class_name(type(self))}[int](...) or infer the type with {class_name(type(self))}.of_iterable().")
        if isinstance(generic_item_type, TypeVar):
            raise TypeError(f"{class_name(type(self))} was instantiated without a proper generic type, somehow {generic_item_type.__name__} was a TypeVar.")

        if (
            len(values) == 1 # If the values are a length 1 tuple
            and not _validate_type(values[0], generic_item_type) # Whose only element doesn't validate the expected type
            and isinstance(values[0], Iterable) # While that element being an Iterable
            and not isinstance(values[0], (str, bytes)) # But not a str or bytes iterable
        ):
            values = values[0]  # Then, the values are unpacked.

        forbidden_iterable_types = _forbidden_iterable_types or getattr(type(self), '_forbidden_iterable_types', ())

        if isinstance(values, forbidden_iterable_types):
            raise TypeError(f"Invalid values type: {class_name(type(values))} for class {class_name(type(self))}.")

        object.__setattr__(self, 'item_type', generic_item_type)

        finisher: Callable[[Iterable[T]], CollectionProtocol[T]] = _finisher or getattr(type(self), '_finisher', lambda x : x)
        skip_validation_finisher: Callable[[Iterable[T]], CollectionProtocol[T]] = getattr(type(self), '_skip_validation_finisher', None) or finisher

        final_values = skip_validation_finisher(values) if _skip_validation else _validate_or_coerce_iterable(values, self.item_type, _coerce=_coerce, _finisher=finisher)

        object.__setattr__(self, 'values', final_values)

    @classmethod
    def _inferred_item_type(cls: type[Collection[T]]) -> type[T] | None:
        """
        Returns the generic type argument T with which this Collection subclass was parameterized, or None.

        This method is used internally for runtime type enforcement and generic introspection, as it fetches the generic
        type from the first position of the _args tuple attribute the class inherits from GenericBase, which is set on
        its __class_getitem__ method.

        :return: The generic type T that this class was called upon, or, if unable to retrieve it, None.
        :rtype: type[T] | None
        """
        try:
            return cls._args[0]
        except (AttributeError, IndexError, TypeError, KeyError):
            return None

    @classmethod
    def of_values[C: Collection](cls: type[C], *values: Any) -> C:
        """
        Creates a Collection object containing the given values, inferring their common type if needed.

        Acts as a type-safe factory method for constructing properly parameterized collections when the type is not
        known beforehand.

        :param values: Values to store in the Collection, received as an iterable or one by one.
        :type values: Any

        :return: A new Collection that is an instance of cls containing the passed values, inferring its item type.
        :rtype: C

        :raises TypeError: If no values are provided.
        """
        return cls.of_iterable(values)


    @classmethod
    def of_iterable[C: Collection](cls: type[C], values: Iterable) -> C:
        """
        Creates a Collection object containing the values of the given iterable, inferring their common type if needed.

        :param values: Iterable containing the desired values.
        :type values: Iterable

        :return: A new Collection that is an instance of cls containing the values of the iterable, inferring its type.
        :rtype: C

        :raises TypeError: If the values Iterable is empty.
        """
        class_generic_type: type | None = cls._inferred_item_type()

        # Called like MutableList[int].of_iterable(...) -> values can be empty since the type is given.
        if class_generic_type is not None:
            return cls(values)

        # Called like MutableList.of_iterable(...) -> values mustn't be empty to infer the type.
        else:
            if not isinstance(values, Sized):
                values = list(values)
            if not values:
                raise TypeError(f"No type could be inferred from the values: {values}")
            from type_validation.type_inference import _infer_type_contained_in_iterable
            return cls[_infer_type_contained_in_iterable(values)](values, _skip_validation=True)

    @classmethod
    def empty[C: Collection](cls: type[C]) -> C:
        """
        Creates an empty Collection subclass of the current class, parameterized with its generic type.

        Useful for initialization of empty collections with known type context, like MutableList[int].empty(). Note
        that calling MutableList.empty() will raise a ValueError.

        :return: An empty Collection that is an instance of this class, keeping its generic type too.
        :rtype: C

        :raises ValueError: If the class calling this method has no generic type on its _args attribute.
        """
        if cls._inferred_item_type() is None:
            raise ValueError(f"Trying to call {class_name(cls)}.empty() without a generic type.")
        return cls()

    def __len__(self) -> int:
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

    def __contains__(self: Collection[T], item: T) -> bool:
        """
        Returns True if the provided item is contained in the Collection's internal container.

        :return: True if the item is contained in the collection's values. False otherwise.
        :rtype: bool
        """
        return item in self.values

    def __eq__(self, other) -> bool:
        """
        Checks if two Collections are equal comparing their values and item type.

        :return: True if other is of a comparable class to self's class, has the same item_type and the same values
         after applying the class's _eq_finisher callable attribute to them.
        :rtype: bool
        """
        if (
            self.item_type != other.item_type
            or not isinstance(other, getattr(type(self), '_comparable_types', Collection))
            or not isinstance(self, getattr(type(other), '_comparable_types', Collection))
        ):
            return False

        from type_validation.type_hierarchy import _resolve_type_priority
        winner_cls = _resolve_type_priority(type(self), type(other))
        eq_finisher: Callable[[Iterable], CollectionProtocol] = getattr(winner_cls, '_eq_finisher', lambda x : x)
        return eq_finisher(self.values) == eq_finisher(other.values)

    def __repr__(self) -> str:
        """
        Returns a string representation of the Collection, showing its generic type name and contained values.

        :return: A string representation of the object, applying the _repr_finisher callable attribute of the class
         to the values before showing them.
        :rtype: str
        """
        repr_finisher: Callable[[Iterable], Iterable] = getattr(type(self), '_repr_finisher', lambda x : x)
        return f"{class_name(type(self))}{repr_finisher(self.values)}"

    def __bool__(self) -> bool:
        """
        Returns a boolean interpretation of the Collection delegating to the underlying container's __bool__ method.

        :return: True if the Collection contains at least one value, False otherwise.
        :rtype: bool
        """
        return bool(self.values)

    def copy[C: Collection](self: C, deep: bool = False) -> C:
        """
        Returns a shallow or deep copy of the Collection.

        If the underlying values implement `.copy()`, it uses that method. Otherwise, directly references the original
        values or uses `deepcopy` if requested. Skips re-validation for performance.

        :param deep: Boolean state parameter to control if the copy is shallow or deep.
        :type deep: bool

        :return: A shallow or deep copy of the object.
        :rtype: C
        """
        if deep:
            from copy import deepcopy
            copied_values = deepcopy(self.values)
        else:
            copied_values = self.values.copy() if hasattr(self.values, 'copy') else self.values
        return type(self)(copied_values, _skip_validation=True)

    def to_list(self: Collection[T]) -> list[T]:
        """
        Returns the contents of the Collection as a built-in list.

        :return: A list containing the values of the Collection.
        :rtype: list[T]
        """
        return list(self.values)

    def to_tuple(self: Collection[T]) -> tuple[T, ...]:
        """
        Returns the contents of the Collection as a built-in tuple.

        :return: A tuple containing the values of the Collection.
        :rtype: tuple[T, ...]
        """
        return tuple(self.values)

    def to_set(self: Collection[T]) -> set[T]:
        """
        Returns the contents of the Collection as a built-in set.

        :return: A set containing the values of the Collection.
        :rtype: set[T]
        """
        return set(self.values)

    def to_frozen_set(self: Collection[T]) -> frozenset[T]:
        """
        Returns the contents of the Collection as a built-in frozenset.

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
        Returns the number of occurrences of the given value in the Collection. Supports unhashable values.

        :param value: Value to count within the Collection.
        :type value: T

        :return: The number of appearances of the value in the Collection. If the underlying container supports
         .count, it uses that method; otherwise, falls back to manual equality counting.
        :rtype: int
        """
        try:
            return self.values.count(value)
        except (AttributeError, TypeError, ValueError):
            return sum(1 for v in self.values if v == value)

    def find_any(self: Collection[T]) -> T:
        """
        Gets a random element from the collection, not defaulting to last insertion or last position.

        :return: A random element of the collection.
        :rtype: T
        """
        from random import choice
        return choice(_convert_to(tuple)(self.values))

    # Functional Methods:

    def map[C: Collection](
        self: C,
        f: Callable[[T], Any],
        result_type: type | None = None,
        *,
        _coerce: bool = False
    ) -> C:
        """
        Maps each value of the Collection to its image by the function `f` and returns a new Collection of them.

        :param f: Callable object to map the Collection with.
        :type f: Callable[[T], Any]

        :param result_type: Type expected to be returned by the Callable. If None, it will be inferred.
        :type result_type: type | None

        :param _coerce: State parameter that if True, tries to coerce results to the result_type if it's not None.
        :type _coerce: bool

        :return: A new Collection of the same subclass as self containing those values. If result_type is given,
         it is used as the item_type of the returned Collection, if not that is inferred from the mapped values.
        :rtype: C
        """
        from abstract_classes.generic_base import base_class
        mapped_values = [f(value) for value in self.values]
        collection_subclass = base_class(self)
        return (
            collection_subclass[result_type](mapped_values, _coerce=_coerce)
            if result_type is not None
            else collection_subclass.of_iterable(mapped_values)
        )

    def flatmap[C: Collection](
        self: C,
        f: Callable[[T], Iterable],
        result_type: type | None = None,
        *,
        _coerce: bool = False
    ) -> C:
        """
        Maps and flattens each element of the Collection and returns a new Collection containing the results.

        Requires that f returns an iterable (excluding str and bytes) for each element.

        :param f: Callable object to map the Collection with.
        :type f: Callable[[T], Iterable]

        :param result_type: Type of Iterable expected to be returned by the Callable. If None, it will be inferred.
        :type result_type: type | None

        :param _coerce: State parameter to try to force coercion to the expected result type if it's not None.
        :type _coerce: bool

        :return: A new Collection of the same subclass as self containing those values. If result_type is given,
         it is used as the type of the returned Collection, if not that is inferred.
        :rtype: C
        """
        from abstract_classes.generic_base import base_class
        flattened = []
        for value in self.values:
            result = f(value)
            if not isinstance(result, Iterable) or isinstance(result, (str, bytes)):
                raise TypeError("flatmap function must return a non-string iterable")
            flattened.extend(result)
        collection_subclass = base_class(self)
        return (
            collection_subclass[result_type](flattened, _coerce=_coerce)
            if result_type is not None
            else collection_subclass.of_iterable(flattened)
        )

    def filter[C: Collection](self: C, predicate: Callable[[T], bool]) -> C:
        """
        Filter the collection by a predicate function.

        :param predicate: A function from the type of the collection to the booleans that the kept values will satisfy.
        :type predicate: Callable[[T], bool]
        :return: A filtered collection containing only the values that were evaluated to True by the predicate.
        :rtype: C
        """
        return type(self)([value for value in self.values if predicate(value)], _skip_validation=True)

    def all_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if all elements in the Collection satisfy the given predicate.

        :param predicate: A function from the type of the collection to the booleans.
        :type predicate: Callable[[T], bool]

        :return: True if all elements match the predicate, False otherwise.
        :rtype: bool
        """
        return all(predicate(value) for value in self.values)

    def any_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if any element in the Collection satisfies the given predicate.

        :param predicate: A function from the type of the collection to the booleans.
        :type predicate: Callable[[T], bool]

        :return: True if at least one element matches the predicate, False otherwise.
        :rtype: bool
        """
        return any(predicate(value) for value in self.values)

    def none_match(self: Collection[T], predicate: Callable[[T], bool]) -> bool:
        """
        Returns True if no element in the Collection satisfies the given predicate.

        :param predicate: A function from the type of the collection to the booleans.
        :type predicate: Callable[[T], bool]

        :return: True if no elements match the predicate, False otherwise.
        :rtype: bool
        """
        return not any(predicate(value) for value in self.values)

    def reduce(self: Collection[T], f: Callable[[T, T], T], unit: T = _MISSING) -> T:
        """
        Reduces the Collection to a single value using a binary operator function and an optional initial unit.

        :param f: A binary operator that combines two elements of the type of the collection into one.
        :type f: Callable[[T, T], T]

        :param unit: Optional initial value for the reduction. If provided, the reduction starts with this.
        :type unit: T | None

        :return: The result of the reduction, as done after being delegated to functools's reduce() function applied to
         the internal container.
        :rtype: T
        """
        from type_validation.type_validation import _validate_type

        if unit is _MISSING:  # unit not passed
            return reduce(f, self.values)

        if not _validate_type(unit, self.item_type):
            raise TypeError(
                f"The unit provided {unit} was of type {class_name(unit)} "
                f"instead of {class_name(self.item_type)}"
            )

        return reduce(f, self.values, unit)

    def for_each(self: Collection[T], consumer: Callable[[T], None]) -> None:
        """
        Performs the given consumer function on each element in the Collection.

        :param consumer: A function that takes an element of type T and returns None.
        :type consumer: Callable[[T], None]
        """
        for value in self.values:
            consumer(value)

    def peek[C: Collection](self: C, consumer: Callable[[T], None]) -> C:
        """
        Performs the given consumer function on each element for side effects and returns the original Collection.

        :param consumer: A function that takes an element of type T and returns None.
        :type consumer: Callable[[T], None]

        :return: The original collection (self).
        :rtype: C
        """
        for item in self.values:
            consumer(item)
        return self

    def distinct[K, C: Collection](self: C, key: Callable[[T], K] = _MISSING) -> C:
        """
        Returns a new Collection with only distinct elements, determined by a key function.

        :param key: A function to extract a comparison key from each element. Defaults to identity mapping.
        :type key: Callable[[T], K]

        :return: A Collection of the same dynamic subclass as self with duplicates removed based on the key.
        :rtype: C
        """
        if key is _MISSING:
            if isinstance(self.values, (set, frozenset)):
                return type(self)(self.values, _skip_validation=True)
            key = lambda x : x

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

    def max(
        self: Collection[T],
        *,
        default: T = _MISSING,
        key: Callable[[T], Any] = None
    ) -> T | None:
        """
        Returns the maximum element in the collection, optionally using a key function or default value.

        :param default: A value to return if the collection is empty.
        :type default: T | None

        :param key: A function to extract a comparison key from each element.
        :type key: Callable[[T], Any]

        :return: The maximum element, or default if provided and self is empty.
        :rtype: T | None
        """
        if default is not _MISSING:
            return max(self.values, default=default, key=key)
        return max(self.values, key=key)

    def min(
        self: Collection[T],
        *,
        default: T = _MISSING,
        key: Callable[[T], Any] = None
    ) -> T | None:
        """
        Returns the minimum element in the collection, optionally using a key function or default.

        :param default: A value to return if the collection is empty.
        :type default: T

        :param key: A function to extract a comparison key from each element.
        :type key: Callable[[T], Any], optional

        :return: The minimum element, or default if provided and self is empty.
        :rtype: T | None
        """
        if default is not _MISSING:
            return min(self.values, default=default, key=key)
        return min(self.values, key=key)

    def group_by[K, C: Collection](
        self: C,
        key: Callable[[T], K]
    ) -> dict[K, C]:
        """
        Groups the items in the Collection on a dict by their value by the key function.

        :param key: Callable to group the items by.
        :type key: Callable[[T], K]

        :return: A dict mapping each value of key onto a Collection of the same dynamic subclass as self containing the
         items that were mapped to that value by the key function.
        :rtype: dict[K, C]
        """
        groups: dict[K, list[T]] = defaultdict(list)
        for item in self.values:
            groups[key(item)].append(item)
        return {
            key : type(self)(group, _skip_validation=True)
            for key, group in groups.items()
        }

    def partition_by[C: Collection](
        self: C,
        predicate: Callable[[T], bool]
    ) -> dict[bool, C]:
        """
        A specialized binary version of group_by grouping by a predicate to bool.

        :param predicate: Function from the type of the collection to the booleans to partition by.
        :type predicate: Callable[[T], bool]

        :return: A dict whose True key is mapped to a Collection of the same dynamic subclass as self containing all
         items in it that satisfied the predicate, likewise for False.
        :rtype: dict[bool, C]
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
        finisher: Callable[[A], R] = lambda x : x
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
        :type finisher: Callable[[A], S]

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
        finisher: Callable[[A, S], R] = lambda x, _ : x
    ) -> R:
        """
        A generalized collector with internal state, inspired by Java's Stream API.

        The supplier gives the initial container for the result. The state_supplier the initial value for the state.
        For each item in self, the accumulator is called on the container, item and state to process the item and
        modify the state, or not, then the finisher is applied to the container and state before returning.

        The implementation of this method is delegated to the non-stateful collect, but it'd be equivalent to::

            acc = supplier()
            state = state_supplier()
            for item in self.values:
                accumulator(acc, state, item)
            return finisher(acc, state)

        :param supplier: Provides the initial container.
        :type supplier: Callable[[], A]

        :param state_supplier: Provides the initial state object.
        :type state_supplier: Callable[[], S]

        :param accumulator: Accepts (accumulator, state, item) to process each item via secondary effects.
        :type accumulator: Callable[[A, S, T], None]

        :param finisher: Final transformation combining accumulator and state to a result.
        :type finisher: Callable[[A, S], R]

        :return: The final collected result.
        :rtype: R
        """
        return self.collect(
            supplier=lambda: (supplier(), state_supplier()),
            accumulator=lambda acc_state, item : accumulator(*acc_state, item),
            finisher=lambda acc_state : finisher(*acc_state)
        )

    def stateful_collect_pure[A, S, R](
        self: Collection[T],
        supplier: Callable[[], A],
        state_supplier: Callable[[], S],
        accumulator: Callable[[A, S, T], tuple[A, S]],
        finisher: Callable[[A, S], R] = lambda x, _ : x
    ) -> R:
        """
        A generalized collector with internal state, inspired by Java's Stream API.

        The supplier provides an initial value of type A. The state_supplier the initial value of type S for the state.
        For each item in self, the accumulator is called on the container, item and state to process the item and
        return the value and state, then the finisher is applied to the last value and state before returning.

        The implementation of this method is delegated to the non-stateful collect, but it'd be equivalent to::

            acc = supplier()
            state = state_supplier()
            for item in self.values:
                acc, state = accumulator(acc, item, state)
            return finisher(acc, state)

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
        return self.collect_pure(
            supplier=lambda: (supplier(), state_supplier()),
            accumulator=lambda acc_state, item: accumulator(*acc_state, item),
            finisher=lambda acc_state: finisher(*acc_state)
        )


@forbid_instantiation
class MutableCollection[T](Collection):
    """
    Abstract class representing a mutale collection of items of type T.

    It adds methods allowing for mutation of the collection without relying on additional structure like an order on
    lists or hashing on sets. Because of that, it's a shallow class containing few methods that can safely be
    implemented this way, and many of those are overridden on its child classes too.

    Attributes:
        item_type (type[T]): The type of elements stored in the collection, derived from the generic type.

        values (CollectionProtocol[T]): The internal container of stored values, usually of one of Python's
         built-in Iterables. It's expected that it implements __len__, __contains__ and __iter__, as well as remove and
         clear.
    """

    item_type: type[T]
    values: MutableCollectionProtocol[T]

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

    def clear(self) -> None:
        """
        Remove all elements from the collection.
        """
        self.values.clear()

    def pop_random(self: MutableCollection[T]) -> T:
        """
        Removes a random element from the collection and returns it.

        :return: A random element from the collection, which is removed from it.
        :rtype: T
        """
        popped_item: T = self.find_any()
        self.remove(popped_item)
        return popped_item

    def filter_inplace(self, predicate: Callable[[T], bool]) -> None:
        """
        Skeletal implementation of a filter inplace of the collection, valid for both a list and set of values.

        :param predicate: Function to the booleans to filter the collection by.
        :type predicate: Callable[[T], bool]
        """
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
        """
        Maps each value in the collection to their image by the function f.

        The class must implement replace_many and in case it's a Sequence, it should respect its ordering.

        :param f: Mapping to apply to the Collection.
        :type f: Callable[[T], T]

        :param _coerce: State parameter that, if True, attempts to coerce the new values to the collection's item type.
        :type _coerce: bool

        :raises AttributeError: If self's class doesn't implement replace_many.
        """
        replace_many = getattr(self, "replace_many", None)
        if callable(replace_many):
            replace_many({x : f(x) for x in self.values}, _coerce=_coerce)
        else:
            raise AttributeError(f"{class_name(type(self))} doesn't implement the replace_many method!")

    def remove_all(self: MutableCollection[T], items: Iterable[T]) -> None:
        """
        Removes from the collection all values within an iterable. On sequences, removes all occurrences of those values.

        :param items: Iterable of items to remove.
        :type items: Iterable[T]
        """
        self.filter_inplace(lambda x : x not in items)

    def retain_all(self: MutableCollection[T], items: Iterable[T]) -> None:
        """
        Removes from the collection all values except the ones present in the given iterable.

        :param items: Iterable of items to keep.
        :type items: Iterable[T]
        """
        self.filter_inplace(lambda x : x in items)