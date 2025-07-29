from __future__ import annotations

from typing import ClassVar, Callable, Iterable, Any, Mapping

from abstract_classes.collection import Collection, MutableCollection
from abstract_classes.generic_base import forbid_instantiation


@forbid_instantiation
class AbstractSet[T](Collection[T]):
    """
    Abstract base class for hashable Collections of type T supporting set operations.

    This class extends Collection, providing standard set-theoretic operations (union, intersection, difference,
    symmetric difference) and comparison methods specifically tailored to sets.

    It is still an abstract class, so it must be subclassed to create concrete implementations.

    This class will be further extended by AbstractMutableSet, adding mutability capabilities to it.

    Attributes:
        _finisher (ClassVar[Callable[[Iterable], Iterable]]): Overrides the _finisher parameter of Collection's init
         by its value, setting it to frozenset.
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
            and self.values == other.values
        )

    def __lt__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a proper subset of another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a proper subset of `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values < other.values
        if isinstance(other, (set, frozenset)):
            return self.values < other
        return NotImplemented

    def __le__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a subset (or equal to) another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a subset or equal to `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values <= other.values
        if isinstance(other, (set, frozenset)):
            return self.values <= other
        return NotImplemented

    def __gt__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a proper superset of another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a proper superset of `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values > other.values
        if isinstance(other, (set, frozenset)):
            return self.values > other
        return NotImplemented

    def __ge__(self: AbstractSet[T], other: Any) -> bool:
        """
        Checks whether this set is a superset (or equal to) another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a superset or equal to `other`, False otherwise.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            return self.values >= other.values
        if isinstance(other, (set, frozenset)):
            return self.values >= other
        return NotImplemented

    def __or__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the union of two AbstractSet instances.

        :param other: The set to union with.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements from both sets.
        :rtype: AbstractSet[T]
        """
        from type_validation.type_validation import _validate_or_coerce_iterable
        return type(self)(self.values | _validate_or_coerce_iterable(other.values, self.item_type, _finisher=set), _skip_validation=True)

    def __and__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the intersection of two AbstractSet instances.

        :param other: The set to intersect with.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements present in both sets.
        :rtype: AbstractSet[T]
        """
        from type_validation.type_validation import _validate_or_coerce_iterable
        return type(self)(self.values & _validate_or_coerce_iterable(other.values, self.item_type, _finisher=set), _skip_validation=True)

    def __sub__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the difference between two AbstractSet instances.

        :param other: The set whose elements to subtract.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements of self not present
        in `other`.
        :rtype: AbstractSet[T]
        """
        from type_validation.type_validation import _validate_or_coerce_iterable
        return type(self)(self.values - _validate_or_coerce_iterable(other.values, self.item_type, _finisher=set), _skip_validation=True)

    def __xor__(self: AbstractSet[T], other: AbstractSet[T]) -> AbstractSet[T]:
        """
        Computes the symmetric difference between two AbstractSet instances.

        :param other: The set to symmetric-difference with.
        :type other: AbstractSet[T]

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements in either set but not both.
        :rtype: AbstractSet[T]
        """
        from type_validation.type_validation import _validate_or_coerce_iterable
        return type(self)(self.values ^ _validate_or_coerce_iterable(other.values, self.item_type, _finisher=set), _skip_validation=True)

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
        return type(self)(self.values.union(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)), _skip_validation=True)

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
        return type(self)(self.values.intersection(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)), _skip_validation=True)

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
        return type(self)(self.values.difference(*_validate_or_coerce_iterable_of_iterables(others, self.item_type,_coerce=_coerce)), _skip_validation=True)

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
        return type(self)(new_values, _skip_validation=True)

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
        from type_validation.type_validation import _validate_or_coerce_iterable
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.issubset(
            _validate_or_coerce_iterable(
                other,
                self.item_type,
                _coerce=_coerce,
                _finisher=set
            )
        )

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
        from type_validation.type_validation import _validate_or_coerce_iterable
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.issuperset(
            _validate_or_coerce_iterable(
                other,
                self.item_type,
                _coerce=_coerce,
                _finisher=set
            )
        )

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
        from type_validation.type_validation import _validate_or_coerce_iterable
        if not _coerce and isinstance(other, Collection) and other.item_type != self.item_type:
            return False
        return self.values.isdisjoint(
            _validate_or_coerce_iterable(
                other,
                self.item_type,
                _coerce=_coerce,
                _finisher=set
            )
        )


@forbid_instantiation
class AbstractMutableSet[T](AbstractSet[T], MutableCollection[T]):
    """
    Abstract base class for mutable, hashable Collections of type T.

    This class extends AbstractSet and adds methods capable of mutating its underlying internal container, such as
    various updates and in-place operations.

    It is still an abstract class, so it must be subclassed to create concrete implementations.

    Attributes:
        _finisher (ClassVar[Callable[[Iterable], Iterable]]): Overrides the _finisher parameter of Collection's init
         by its value, setting it to set to ensure mutability of the underlying container.

        _mutable (ClassVar[bool]): Metadata attribute describing the mutability of this class. For now, it's unused.
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
        Update the set so it contains the elements that are in exactly one of the sets from among self and others.

        :param others: One or more iterables or Collections to symmetrically differ with.
        :type others: Iterable[T] | Collection[T]

        :param _coerce: State parameter that, if True, attempts to coerce all elements before processing.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            self.values.symmetric_difference_update(validated_set)

    def filter_inplace(self, predicate: Callable[[T], bool]) -> None:
        """
        Filters this set, keeping only the values that satisfy the predicate.

        :param predicate: Function to the booleans to filter the set by.
        :type predicate: Callable[[T], bool]
        """
        self.values.difference_update({x for x in self.values if not predicate(x)})

    def replace(
        self: AbstractMutableSet[T],
        old: T,
        new: T,
        *,
        _coerce: bool = False,
        _remove_if_new_is_present: bool = False
    ) -> None:
        """
        Replaces all appearances of `old` to `new`.

        :param old: Value to replace
        :type old: T

        :param new: Value to replace it by.
        :type new: T

        :param _coerce: State parameter that, if True, attempts to coerce the new value to the set's item type.
        :type _coerce: bool

        :param _remove_if_new_is_present: State parameter that makes it so that the old value is removed even when the
         new is already present.
        :type _remove_if_new_is_present: bool
        """
        if old not in self.values:
            return

        from type_validation.type_validation import _validate_or_coerce_value
        new = _validate_or_coerce_value(new, self.item_type, _coerce=_coerce)

        if _remove_if_new_is_present:
            self.values.remove(old)
            self.values.add(new)
        else:
            if new not in self.values:
                self.values.add(new)
                self.values.remove(old)

    def replace_many(
        self: AbstractMutableSet[T],
        replacements: dict[T, T] | Mapping[T, T],
        *,
        _coerce: bool = False
    ) -> None:
        """
        Replaces each value in the given dict's keys for its value.

        :param replacements: Dict of pairs old : new to replace.
        :type replacements: dict[T, T]

        :param _coerce: State parameter that, if True, attempts to coerce the new values to self's item type.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_value

        validated_replacements = {
            old: _validate_or_coerce_value(new, self.item_type, _coerce=_coerce)
            for old, new in replacements.items()
        }

        to_remove = set(validated_replacements.keys()) & self.values
        to_add = {validated_replacements[old] for old in to_remove}

        self.values.difference_update(to_remove)
        self.values.update(to_add)
