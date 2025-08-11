from __future__ import annotations

import collections
import typing
from typing import ClassVar, Callable, Iterable, Any, Mapping

from abstract_classes.collection import Collection, MutableCollection
from abstract_classes.generic_base import forbid_instantiation, _convert_to, class_name


@forbid_instantiation
class AbstractSet[T](Collection):
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

    item_type: type[T]
    values: frozenset[T]

    # Metadata class attributes
    _finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(frozenset)
    _skip_validation_finisher: ClassVar[Callable[[Iterable], Iterable]] = frozenset
    _repr_finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(set)
    _eq_finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(set)
    _priority: ClassVar[int] = 0

    def __lt__(self: AbstractSet, other: AbstractSet) -> bool:
        """
        Checks whether this set is a proper subset of another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: AbstractSet

        :return: True if this set is a proper subset of `other`, False otherwise. When comparing with another
         AbstractSet, their item_type must match exactly.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            if self.item_type != other.item_type:
                from type_validation.type_hierarchy import _is_subtype
                return _is_subtype(self.item_type, other.item_type) and self.values >= other.values
            return self.values < other.values
        return NotImplemented

    def __le__(self: AbstractSet, other: AbstractSet) -> bool:
        """
        Checks whether this set is a subset (or equal to) another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: AbstractSet

        :return: True if this set is a subset or equal to `other`, False otherwise. When comparing with another
         AbstractSet, their item_type must match exactly.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            if self.item_type != other.item_type:
                from type_validation.type_hierarchy import _is_subtype
                return _is_subtype(self.item_type, other.item_type) and self.values >= other.values
            return self.values <= other.values
        return NotImplemented

    def __gt__(self: AbstractSet, other: AbstractSet) -> bool:
        """
        Checks whether this set is a proper superset of another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: Any

        :return: True if this set is a proper superset of `other`, False otherwise. When comparing with another
         AbstractSet, their item_type must match exactly.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            if self.item_type != other.item_type:
                from type_validation.type_hierarchy import _is_subtype
                return _is_subtype(other.item_type, self.item_type) and self.values >= other.values
            return self.values > other.values
        return NotImplemented

    def __ge__(self: AbstractSet, other: AbstractSet) -> bool:
        """
        Checks whether this set is a superset (or equal to) another AbstractSet, set or frozenset.

        :param other: The set to compare against.
        :type other: AbstractSet

        :return: True if this set is a superset or equal to `other`, False otherwise. When comparing with another
         AbstractSet, their item_type must match exactly.
        :rtype: bool
        """
        if isinstance(other, AbstractSet):
            if self.item_type != other.item_type:
                from type_validation.type_hierarchy import _is_subtype
                return _is_subtype(other.item_type, self.item_type) and self.values >= other.values
            return self.values >= other.values
        return NotImplemented

    def __or__[S: AbstractSet](self: S, other: S) -> S:
        """
        Computes the union of two AbstractSet instances.

        In order to preserve the commutativity of the operator, the subclass of the return is determined by which of
        the operands is immutable, and if both or none are, by the _priority class attribute of their type.

        :param other: The set to union with.
        :type other: S

        :return: A new AbstractSet containing all elements from both self and other.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        from type_validation.type_hierarchy import _resolve_type_priority
        set_type = _resolve_type_priority(type(self), type(other))

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _get_supertype
            new_type = _get_supertype(self.item_type, other.item_type)
        else:
            new_type = self.item_type

        return set_type[new_type](self.values | other.values, _skip_validation=True)

    def __and__[S: AbstractSet](self: S, other: S) -> S:
        """
        Computes the intersection of two AbstractSet instances.

        :param other: The set to intersect with.
        :type other: S

        :return: A new AbstractSet containing all elements present in both sets.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        from type_validation.type_hierarchy import _resolve_type_priority
        set_type = _resolve_type_priority(type(self), type(other))

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _get_subtype
            new_type = _get_subtype(self.item_type, other.item_type)
        else:
            new_type = self.item_type

        return set_type[new_type](self.values & other.values, _skip_validation=True)

    def __sub__[S: AbstractSet](self: S, other: Iterable) -> S:
        """
        Computes the difference between two AbstractSet instances.

        :param other: The set whose elements to subtract.
        :type other: Iterable

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements of self not present
         in `other`.
        :rtype: S
        """
        from type_validation.type_validation import _validate_or_coerce_iterable
        return type(self)(self.values - _validate_or_coerce_iterable(other, self.item_type, _finisher=set), _skip_validation=True)

    def __xor__[S: AbstractSet](self: S, other: S) -> S:
        """
        Computes the symmetric difference between two AbstractSet instances.

        :param other: The set to symmetric-difference with.
        :type other: Iterable

        :return: A new AbstractSet of the same dynamic subclass as self containing all elements in either set but not both.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        from type_validation.type_hierarchy import _resolve_type_priority
        set_type = _resolve_type_priority(type(self), type(other))

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _get_supertype
            new_type = _get_supertype(self.item_type, other.item_type)
        else:
            new_type = self.item_type

        return set_type[new_type](self.values ^ other.values, _skip_validation=True)

    def union[S: AbstractSet](
        self: S,
        *others: Iterable,
        _coerce: bool = False
    ) -> S:
        """
        Returns the union of this set with one or more iterables, preserving self's item_type.

        The operation is delegated to the underlying container's union method, which should support passing multiple
        iterable arguments.

        :param others: One or more iterables to union with.
        :type others: Iterable

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing all distinct elements of self and
         all the iterables passed.
        :rtype: S
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.union(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)), _skip_validation=True)

    def intersection[S: AbstractSet](
        self: S,
        *others: Iterable,
        _coerce: bool = False
    ) -> S:
        """
        Returns the intersection of this set with one or more iterables, preserving self's item_type.

        The operation is delegated to the underlying container's union method, which should support passing multiple
        iterable arguments.

        :param others: One or more iterables to intersect with.
        :type others: Iterable

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing the elements common to self and all
        passed iterables.
        :rtype: AbstractSet[T]
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.intersection(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce)), _skip_validation=True)

    def difference[S: AbstractSet](
        self: S,
        *others: Iterable,
        _coerce: bool = False
    ) -> S:
        """
        Returns the difference between this set and one or more iterables.

        The operation is delegated to the underlying container's union method, which should support passing multiple
        iterable arguments.

        :param others: One or more iterables to subtract.
        :type others: Iterable

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing its elements that are not present in
         any of the others.
        :rtype: S
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        return type(self)(self.values.difference(*_validate_or_coerce_iterable_of_iterables(others, self.item_type,_coerce=_coerce)), _skip_validation=True)

    def symmetric_difference[S: AbstractSet](
        self: S,
        *others: Iterable,
        _coerce: bool = False
    ) -> S:
        """
        Returns the symmetric difference between this set and one or more iterables, preserving self's item_type.

        :param others: One or more iterables to compare.
        :type others: Iterable

        :param _coerce: State parameter that, if True, attempts to coerce the incoming values.
        :type _coerce: bool

        :return: A new AbstractSet of the same dynamic subclass as self containing the elements that are present in only
        one of self or the passed iterables.
        :rtype: S
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        new_values = self.values
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            new_values = new_values.symmetric_difference(validated_set)
        return type(self)(new_values, _skip_validation=True)

    def is_subset(
        self: AbstractSet,
        other: AbstractSet
    ) -> bool:
        """
        Checks if this set is a subset of another AbstractSet.

        :param other: The set to compare against.
        :type other: AbstractSet

        :return: True if this set is a subset of `other`, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if other.item_type != self.item_type:
            from type_validation.type_hierarchy import _is_subtype
            if not _is_subtype(self.item_type, other.item_type):
                raise ValueError(f"Cannot compare sets of different types: {class_name(self.item_type)} != {class_name(other.item_type)}")
        return self.values.issubset(other.values)

    def is_superset(
        self: AbstractSet,
        other: AbstractSet
    ) -> bool:
        """
        Checks if this set is a superset of another AbstractSet.

        :param other: The set to compare against.
        :type other: AbstractSet

        :return: True if this set is a superset of `other`, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if other.item_type != self.item_type:
            from type_validation.type_hierarchy import _is_subtype
            if not _is_subtype(other.item_type, self.item_type):
                raise ValueError(f"Cannot compare sets of different types: {class_name(self.item_type)} != {class_name(other.item_type)}")
        return self.values.issuperset(other.values)

    def is_disjoint(
        self: AbstractSet,
        other: AbstractSet
    ) -> bool:
        """
        Checks if this set is disjoint with another AbstractSet.

        :param other: The set to compare against.
        :type other: AbstractSet

        :return: True if this set has no elements in common with `other`, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented
        if other.item_type != self.item_type:
            from type_validation.type_hierarchy import _is_subtype
            if not _is_subtype(other.item_type, self.item_type) and not _is_subtype(self.item_type, other.item_type):
                raise ValueError(f"Cannot compare sets of different types: {self.item_type.__name__} != {other.item_type.__name__}")
        return self.values.isdisjoint(other.values)


@forbid_instantiation
class AbstractMutableSet[T](AbstractSet, MutableCollection):
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

    item_type: type[T]
    values: set[T]

    # Metadata class attributes
    _finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(set)
    _skip_validation_finisher: ClassVar[Callable[[Iterable], Iterable]] = set
    _mutable: ClassVar[bool] = True
    _priority: ClassVar[int] = 1

    def __ior__[S: AbstractMutableSet](
        self: S,
        other: AbstractSet
    ) -> S:
        """
        In-place union update with another AbstractSet with the operator |=.

        Contrary to the binary operator |, which, to preserve commutativity chooses the greater subtype of its operands
        as the item type of its return, |= needs not to preserve commutativity, since the item type of self cannot
        under any circumstance be altered.

        :param other: The set to union with.
        :type other: AbstractSet

        :return: This updated AbstractMutableSet.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _is_subtype
            if not _is_subtype(other.item_type, self.item_type):
                raise TypeError(f"Incompatible types between {type(self).__name__} and {type(other).__name__}.")

        self.update(other)
        return self

    def __iand__[S: AbstractMutableSet](
        self: S,
        other: AbstractSet
    ) -> S:
        """
        In-place intersection update with another AbstractSet with the operator &=.

        Contrary to the binary operator &, which, to preserve commutativity chooses the lesser subtype of its operands
        as the item type of its return, &= needs not to preserve commutativity, since the item type of self cannot
        under any circumstance be altered.

        :param other: The set to intersect with.
        :type other: AbstractSet

        :return: This updated AbstractMutableSet.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        self.intersection_update(other)
        return self

    def __isub__[S: AbstractMutableSet](
        self: S,
        other: AbstractSet
    ) -> S:
        """
        In-place difference update with another AbstractSet with the operator -=.

        :param other: The set whose elements should be removed from this set.
        :type other: AbstractSet

        :return: This updated AbstractMutableSet.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        self.difference_update(other)
        return self

    def __ixor__[S: AbstractMutableSet](
        self: S,
        other: AbstractSet
    ) -> S:
        """
        In-place symmetric difference update with another AbstractSet with the operator ^=.

        :param other: The set whose elements should be symmetrically removed from this set.
        :type other: AbstractSet

        :return: This updated AbstractMutableSet.
        :rtype: S
        """
        if not isinstance(other, AbstractSet):
            return NotImplemented

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _is_subtype
            if not _is_subtype(other.item_type, self.item_type):
                raise TypeError(f"Incompatible types between {type(self).__name__} and {type(other).__name__}.")

        self.symmetric_difference_update(other)
        return self

    def add(
        self: AbstractMutableSet[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Add a single element to the set. Delegates the operation to the underlying container's add method.

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
        *others: Iterable[T],
        _coerce: bool = False
    ) -> None:
        """
        Update the set with elements from one or more iterables.

        :param others: One or more iterables or Collections whose elements will be added to this set.
        :type others: Iterable[T]

        :param _coerce: State parameter that, if True, attempts to coerce all elements to the expected type.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def difference_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T],
        _coerce: bool = False
    ) -> None:
        """
        Remove all elements found in one or more provided collections.

        :param others: One or more iterables or Collections whose elements will be removed from this set.
        :type others: Iterable[T]

        :param _coerce: State parameter that, if True, attempts to coerce all elements before removal.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.difference_update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def intersection_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T],
        _coerce: bool = False
    ) -> None:
        """
        Retain only elements that are also in all provided collections.

        :param others: One or more iterables or Collections to intersect and update with.
        :type others: Iterable[T]

        :param _coerce: State parameter that, if True, attempts to coerce all elements before intersection.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        self.values.intersection_update(*_validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce))

    def symmetric_difference_update(
        self: AbstractMutableSet[T],
        *others: Iterable[T],
        _coerce: bool = False
    ) -> None:
        """
        Update the set so it contains the elements that are in exactly one of the sets from among self and others.

        :param others: One or more iterables or Collections to symmetrically differ with.
        :type others: Iterable[T]

        :param _coerce: State parameter that, if True, attempts to coerce all elements before processing.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable_of_iterables
        for validated_set in _validate_or_coerce_iterable_of_iterables(others, self.item_type, _coerce=_coerce):
            self.values.symmetric_difference_update(validated_set)

    def filter_inplace(self: AbstractMutableSet[T], predicate: Callable[[T], bool]) -> None:
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
            old : _validate_or_coerce_value(new, self.item_type, _coerce=_coerce)
            for old, new in replacements.items()
        }

        to_remove = set(validated_replacements.keys()) & self.values
        to_add = {validated_replacements[old] for old in to_remove}

        self.values.difference_update(to_remove)
        self.values.update(to_add)
