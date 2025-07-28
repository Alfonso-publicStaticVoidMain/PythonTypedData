from __future__ import annotations

from typing import ClassVar, Callable, Iterable, Any

from abstract_classes.collection import Collection, MutableCollection
from abstract_classes.generic_base import forbid_instantiation


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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_collection_type_and_get_values
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
        from type_validation.type_validation import _validate_collection_type_and_get_values
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
        from type_validation.type_validation import _validate_collection_type_and_get_values
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.isdisjoint(_validate_collection_type_and_get_values(other, self.item_type, _coerce=_coerce))


@forbid_instantiation
class AbstractMutableSet[T](AbstractSet[T], MutableCollection[T]):
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
        from type_validation.type_validation import _validate_or_coerce_value
        self.values.add(_validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

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
        from type_validation.type_validation import _validate_or_coerce_value
        value_to_remove = value
        if _coerce:
            try:
                value_to_remove = _validate_or_coerce_value(value, self.item_type)
            except (TypeError, ValueError):
                pass
        self.values.discard(value_to_remove)

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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
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
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            self.values.symmetric_difference_update(validated_set)
