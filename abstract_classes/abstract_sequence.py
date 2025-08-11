from __future__ import annotations

import collections
import typing
from typing import ClassVar, Callable, Iterable, Any, Iterator

from abstract_classes.abstract_set import AbstractSet
from abstract_classes.collection import Collection, MutableCollection
from abstract_classes.generic_base import forbid_instantiation, _convert_to


@forbid_instantiation
class AbstractSequence[T](Collection):
    """
    Abstract base class for sequence-like Collections of a type T, with ordering and indexing capabilities.

    Provides standard sequence operations such as indexing, slicing, comparison, addition of other sequences,
    multiplication by integers, and sorting.

    It is still an abstract class, so it must be subclassed to create concrete implementations.

    This class will be further extended by AbstractMutableSequence to add the methods that modify the internal data
    container of the class.

    Attributes:
        _finisher (ClassVar[Callable[[Iterable], Iterable]]): It is applied to the values before setting them as an
         attribute on Collection's init.

        _skip_validation_finisher (ClassVar[Callable[[Iterable], Iterable]]): It is applied to the values before setting
         them as an attribute on Collection's init when the parameter _skip_validation is True.

        _repr_finisher (ClassVar[Callable[[Iterable], Iterable]]): Callable that is applied on the repr method to show
         the values contained on the sequence.

        _eq_finisher (ClassVar[Callable[[Iterable], Iterable]]): Callable that is applied on both self and other's
         values on the eq method to check for equality.

        _forbidden_iterable_types (ClassVar[tuple[type, ...]]): Overrides the _forbidden_iterable_types parameter of
         Collection's init, setting it to (set, frozenset, AbstractSet, typing.AbstractSet).
    """

    item_type: type[T]
    values: tuple[T, ...]

    # Metadata class attributes
    _finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(tuple)
    _skip_validation_finisher: ClassVar[Callable[[Iterable], Iterable]] = tuple
    _repr_finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(list)
    _eq_finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(tuple)
    _forbidden_iterable_types: ClassVar[tuple[type, ...]] = (set, frozenset, AbstractSet, typing.AbstractSet)
    _priority: ClassVar[int] = 0

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
            raise TypeError("Invalid index type: must be an int or slice")

    def __lt__(self: AbstractSequence[T], other: AbstractSequence[T]) -> bool:
        """
        Checks if this sequence is lexicographically less than another.

        :param other: Another AbstractSequence to compare with.
        :type other: AbstractSequence[T]

        :return: True if self is less than `other`.
        :rtype: bool
        """
        if not isinstance(other, AbstractSequence):
            return NotImplemented
        eq_finisher = getattr(type(self), '_eq_finisher', lambda x : x)
        return eq_finisher(self.values) < eq_finisher(other.values)

    def __gt__(self: AbstractSequence[T], other: AbstractSequence[T]) -> bool:
        """
        Checks if this sequence is lexicographically greater than another.

        :param other: Another AbstractSequence to compare with.
        :type other: AbstractSequence[T]

        :return: True if self is greater than `other`.
        :rtype: bool
        """
        if not isinstance(other, AbstractSequence):
            return NotImplemented
        eq_finisher = getattr(type(self), '_eq_finisher', lambda x : x)
        return eq_finisher(self.values) > eq_finisher(other.values)

    def __le__(self: AbstractSequence[T], other: AbstractSequence[T]) -> bool:
        """
        Checks if this sequence is less than or equal to another.

        :param other: Another AbstractSequence to compare with.
        :type other: AbstractSequence[T]

        :return: True if self is less than or equal to `other`.
        :rtype: bool
        """
        if not isinstance(other, AbstractSequence):
            return NotImplemented
        eq_finisher = getattr(type(self), '_eq_finisher', lambda x : x)
        return eq_finisher(self.values) <= eq_finisher(other.values)

    def __ge__(self: AbstractSequence[T], other: AbstractSequence[T]) -> bool:
        """
        Checks if this sequence is greater than or equal to another.

        :param other: Another AbstractSequence to compare with.
        :type other: AbstractSequence[T]

        :return: True if self is greater than or equal to `other`.
        :rtype: bool
        """
        if not isinstance(other, AbstractSequence):
            return NotImplemented
        eq_finisher = getattr(type(self), '_eq_finisher', lambda x : x)
        return eq_finisher(self.values) >= eq_finisher(other.values)

    def __add__[S: AbstractSequence](
        self: S,
        other: S,
    ) -> S:
        """
        Returns a new AbstractSequence concatenating the values of another AbstractSequence, list or tuple.

        :param other: The sequence to concatenate.
        :type other: S

        :return: A new AbstractSequence of the same dynamic subclass as self containing the elements from `other` added
         right after the ones from self, as done by the __add__ method of the underlying container.
        :rtype: S

        :raises TypeError: If `other` has incompatible types.
        """
        if not isinstance(other, AbstractSequence):
            return NotImplemented

        from type_validation.type_hierarchy import _resolve_type_priority
        sequence_type = _resolve_type_priority(type(self), type(other))

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _get_subtype
            new_type = _get_subtype(self.item_type, other.item_type)
        else:
            new_type = self.item_type

        finisher = getattr(sequence_type, '_finisher', list)
        return sequence_type[new_type](finisher(self.values) + finisher(other.values), _skip_validation=True)

    def __mul__[S: AbstractSequence](
        self: S,
        n: int
    ) -> S:
        """
        Returns a new AbstractSequence with the values of this sequence concatenated n times.

        :param n: Number of times to repeat the sequence.
        :type n: int

        :return: A new AbstractSequence of the same dynamic subclass as self with its values concatenated n times.
        :rtype: S

        :raises TypeError: If n is not an integer.
        """
        if not isinstance(n, int):
            return NotImplemented
        return type(self)(self.values * n, _skip_validation=True)

    def __rmul__[S: AbstractSequence](
        self: S,
        n: int
    ) -> S:
        """
        Returns a new AbstractSequence with the values of this sequence concatenated n times.

        :param n: Number of times to repeat the sequence.
        :type n: int

        :return: A new AbstractSequence of the same dynamic subclass as self with its values concatenated n times.
        :rtype: S

        :raises TypeError: If n is not an integer.
        """
        if not isinstance(n, int):
            return NotImplemented
        return type(self)(self.values * n, _skip_validation=True)

    def __reversed__(self: AbstractSequence[T]) -> Iterator[T]:
        """
        Returns a reversed iterator over the sequence, delegated to the __reversed__ method of the underlying container.

        :return: A reversed iterator over the values of the sequence.
        :rtype: Iterator[T]
        """
        return reversed(self.values)

    def reversed[S: AbstractSequence](self: S) -> S:
        """
        Returns a new AbstractSequence with its elements in reverse order.

        :return: A new reversed AbstractSequence of the same dynamic subclass as self containing its elements in
         reversed order.
        :rtype: S
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
        Returns the index of the first occurrence of a value, or a fallback defaulted to -1 if it isn't found.

        :param value: The value to search for.
        :type value: T

        :param fallback: Number to return if the value isn't found. Defaulted to -1.
        :type fallback: int

        :return: Index of the first appearance of the value, or fallback if it isn't found.
        :rtype: int
        """
        try:
            return self.values.index(value)
        except ValueError:
            return fallback

    def sorted[S: AbstractSequence](
        self: S,
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False
    ) -> S:
        """
        Returns a new AbstractSequence with its elements sorted by an optional key.

        :param key: Optional function to extract the comparison key from.
        :type key: Callable[[T], Any] | None

        :param reverse: Whether to sort in descending order.
        :type reverse: bool

        :return: A new AbstractSequence of the same dynamic subclass as self with the same elements but sorted
         according to the key and reverse parameters.
        :rtype: S
        """
        return type(self)(sorted(self.values, key=key, reverse=reverse), _skip_validation=True)


@forbid_instantiation
class AbstractMutableSequence[T](AbstractSequence, MutableCollection):
    """
    Abstract base class for mutable and ordered sequences containing values of a type T.

    This class extends AbstractSequence by adding mutation capabilities such as appending, inserting, removing, and
    sorting.

    It is still an abstract class, so it must be subclassed to create concrete implementations.

    Attributes:
        _finisher (ClassVar[Callable[[Iterable], Iterable]]): Overrides the _finisher parameter of Collection's init
         by its value, setting it to list to ensure mutability of the underlying container.

        _mutable (ClassVar[bool]): Metadata attribute describing the mutability of this class. For now, it's unused.
    """

    item_type: type[T]
    values: list[T]

    # Metadata class attributes
    _finisher: ClassVar[Callable[[Iterable], Iterable]] = _convert_to(list)
    _skip_validation_finisher: ClassVar[Callable[[Iterable], Iterable]] = list
    _allowed_ordered_types: ClassVar[tuple[type, ...]] = (list, tuple, AbstractSequence, range, collections.deque, collections.abc.Sequence)
    _mutable: ClassVar[bool] = True
    _priority: ClassVar[int] = 1

    def append(
        self: AbstractMutableSequence[T],
        value: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Appends a value to the end of the sequence, delegating on the underlying container's append method.

        :param value: The value to append.
        :type value: T

        :param _coerce: State parameter that, if True, attempts to coerce the value into the expected type.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_value
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
        from type_validation.type_validation import _validate_or_coerce_iterable, _validate_or_coerce_value

        if isinstance(index, slice):
            if not isinstance(value, getattr(type(self), '_allowed_ordered_types', ())):
                raise ValueError("You can't assign a value that isn't a sequence to a slice!")
            self.values[index] = _validate_or_coerce_iterable(value, self.item_type, _coerce=_coerce)

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

    def __iadd__[S: AbstractMutableSequence](
        self: S,
        other: AbstractSequence[T]
    ) -> S:
        """
        Appends the elements from `other` to this sequence in-place.

        :param other: The sequence whose elements will be appended.
        :type other: AbstractSequence[T]

        :return: Self after appending the contents of `other`.
        :rtype: S

        :raises TypeError: If `other` contains elements of an incompatible type.
        """
        if not isinstance(other, AbstractSequence):
            return NotImplemented

        if self.item_type != other.item_type:
            from type_validation.type_hierarchy import _is_subtype
            if not _is_subtype(other.item_type, self.item_type):
                raise TypeError(f"Incompatible types between {type(self).__name__} and {type(other).__name__}.")

        self.values.extend(other.values)
        return self

    def __imul__[S: AbstractMutableSequence](self: S, n: int) -> S:
        """
        Concatenates the contents of this sequence n times in-place.

        :param n: The number of times to repeat the sequence.
        :type n: int

        :return: Self after concatenation.
        :rtype: S

        :raises TypeError: If `n` is not an integer.
        """
        if not isinstance(n, int):
            return NotImplemented
        self.values[:] = self.values * n
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

    def reverse(self: AbstractMutableSequence[T]) -> None:
        """
        Reverses the order of this sequence in-place.
        """
        self.values.reverse()

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
        from type_validation.type_validation import _validate_or_coerce_value
        self.values.insert(index, _validate_or_coerce_value(value, self.item_type, _coerce=_coerce))

    def extend(
        self: AbstractMutableSequence[T],
        other: Iterable[T],
        *,
        _coerce: bool = False
    ) -> None:
        """
        Extends the sequence appending the elements from another iterable.

        :param other: The iterable whose elements to add.
        :type other: Iterable[T]

        :param _coerce: If True, attempts to coerce each value into the expected type.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable
        self.values.extend(_validate_or_coerce_iterable(other, self.item_type, _coerce=_coerce))

    def pop(self: AbstractMutableSequence[T], index: int = -1) -> T:
        """
        Removes and returns the item at the given position (default at the last position).

        :param index: Index of the element to remove. Defaults to -1 (last element).
        :type index: int

        :return: The removed element, as returned by the underlying container's pop method.
        :rtype: T
        """
        return self.values.pop(index)

    def filter_inplace(self: AbstractMutableSequence[T], predicate: Callable[[T], bool]) -> None:
        """
        Filters this sequence, keeping only the values that satisfy the predicate, preserving their order.

        Overrides the method from the parent class MutableCollection, which is implemented in a skeletal and inefficient
        way to work with both lists and sets as underlying containers.

        :param predicate: Function to the booleans to filter the sequence by.
        :type predicate: Callable[[T], bool]
        """
        self.values[:] = [item for item in self.values if predicate(item)]

    def replace(
        self: AbstractMutableSequence[T],
        old: T,
        new: T,
        *,
        _coerce: bool = False
    ) -> None:
        """
        Replaces all appearances of `old` to `new`, respecting their position within the sequence.

        :param old: Value to replace
        :type old: T

        :param new: Value to replace it by.
        :type new: T

        :param _coerce: State parameter that, if True, attempts to coerce the new value to the sequence's item type.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_value
        new = _validate_or_coerce_value(new, self.item_type, _coerce=_coerce)
        self.values[:] = [new if item == old else item for item in self.values]

    def replace_many(
        self: AbstractMutableSequence[T],
        replacements: dict[T, T] | typing.Mapping[T, T],
        *,
        _coerce: bool = False
    ) -> None:
        """
        Replaces each value in the given dict's keys for its value, respecting its position within the sequence.

        :param replacements: Dict of pairs old : new to replace.
        :type replacements: dict[T, T]

        :param _coerce: State parameter that, if True, attempts to coerce the new values to self's item type.
        :type _coerce: bool
        """
        from type_validation.type_validation import _validate_or_coerce_value
        validated_replacements = {old : _validate_or_coerce_value(new, self.item_type, _coerce=_coerce) for old, new in replacements.items()}
        self.values[:] = [validated_replacements.get(item, item) for item in self.values]
