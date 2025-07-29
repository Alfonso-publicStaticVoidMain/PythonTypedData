from __future__ import annotations

import typing
from typing import ClassVar, Callable, Iterable, Any, Iterator

from abstract_classes.abstract_set import AbstractSet
from abstract_classes.collection import Collection, MutableCollection
from abstract_classes.generic_base import forbid_instantiation


@forbid_instantiation
class AbstractSequence[T](Collection[T]):
    """
    Abstract base class for sequence-like Collections of a type T, with ordering and indexing capabilities.

    Provides standard sequence operations such as indexing, slicing, comparison, addition of other sequences,
    multiplication by integers, and sorting.

    It is still an abstract class, so it must be subclassed to create concrete implementations.

    This class will be further extended by AbstractMutableSequence to add the methods that modify the internal data
    container of the class.

    Attributes:
        _finisher (ClassVar[Callable[[Iterable], Iterable]]): Overrides the _finisher parameter of Collection's init
         by its value, setting it to tuple.

        _forbidden_iterable_types (ClassVar[tuple[type, ...]]): Overrides the _forbidden_iterable_types parameter of
         Collection's init, setting it to (set, frozenset, AbstractSet, typing.AbstractSet).
    """

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = tuple
    _forbidden_iterable_types: ClassVar[tuple[type, ...]] = (set, frozenset, AbstractSet, typing.AbstractSet)

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

    def __eq__(self: AbstractSequence[T], other: Any) -> bool:
        """
        Checks equality with another sequence based on their item type and values.

        Do note that equality will hold when comparing different implementations of AbstractSequence as long as the
        item type is the same and the values are the same, even if holt by different containers.

        :param other: Object to compare against.
        :type other: Any

        :return: True if `other` is an AbstractSequence with the same item type and the same values on the same order.
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

        :param other: Another AbstractSequence, list or tuple to compare with.
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

        :param other: Another AbstractSequence, list or tuple to compare with.
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

        :param other: Another AbstractSequence, list or tuple to compare with.
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

        :param other: Another AbstractSequence, list or tuple to compare with.
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
        Returns a new AbstractSequence concatenating the values of another AbstractSequence, list or tuple.

        :param other: The sequence or iterable to concatenate.
        :type other: AbstractSequence[T] | list[T] | tuple[T]

        :return: A new AbstractSequence of the same dynamic subclass as self containing the elements from `other` added
         right after the ones from self, as done by the __add__ method of the underlying container.
        :rtype: AbstractSequence[T]

        :raises TypeError: If `other` has incompatible types.
        """
        from type_validation.type_validation import _validate_collection_type_and_get_values
        if not isinstance(other, (AbstractSequence, list, tuple)):
            return NotImplemented
        return type(self)(self.values + _validate_collection_type_and_get_values(other, self.item_type))

    def __mul__(
        self: AbstractSequence[T],
        n: int
    ) -> AbstractSequence[T]:
        """
        Returns a new AbstractSequence with the values of this sequence concatenated n times.

        :param n: Number of times to repeat the sequence.
        :type n: int

        :return: A new AbstractSequence of the same dynamic subclass as self with its values concatenated n times.
        :rtype: AbstractSequence[T]

        :raises TypeError: If n is not an integer.
        """
        if not isinstance(n, int):
            return NotImplemented
        return type(self)(self.values * n, _skip_validation=True)

    def __sub__(self: AbstractSequence[T], other: Iterable[T]) -> AbstractSequence[T]:
        """
        Returns a new AbstractSequence with the elements of `other` removed.

        :param other: A collection of elements to exclude.
        :type other: Iterable

        :return: A new AbstractSequence of the same dynamic subclass as self with all elements present in `other` removed.
        :rtype: AbstractSequence[T]
        """
        return self.filter(lambda item : item not in other)

    def __reversed__(self: AbstractSequence[T]) -> Iterator[T]:
        """
        Returns a reversed iterator over the sequence, delegated to the __reversed__ method of the underlying container.

        :return: A reversed iterator over the values of the sequence.
        :rtype: Iterator[T]
        """
        return reversed(self.values)

    def reversed(self) -> AbstractSequence[T]:
        """
        Returns a new AbstractSequence with its elements in reverse order.

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

    def sorted(
        self: AbstractSequence[T],
        *,
        key: Callable[[T], Any] | None = None,
        reverse: bool = False
    ) -> AbstractSequence[T]:
        """
        Returns a new AbstractSequence with its elements sorted by an optional key.

        :param key: Optional function to extract the comparison key from.
        :type key: Callable[[T], Any] | None

        :param reverse: Whether to sort in descending order.
        :type reverse: bool

        :return: A new AbstractSequence of the same dynamic subclass as self with the same elements but sorted
        according to the key and reverse parameters.
        :rtype: AbstractSequence[T]
        """
        return type(self)(sorted(self.values, key=key, reverse=reverse), _skip_validation=True)


@forbid_instantiation
class AbstractMutableSequence[T](AbstractSequence[T], MutableCollection[T]):
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

    _finisher: ClassVar[Callable[[Iterable], Iterable]] = list
    _mutable: ClassVar[bool] = True

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
        from type_validation.type_validation import _validate_collection_type_and_get_values, _validate_or_coerce_value

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
        if not isinstance(other, (AbstractSequence, list, tuple)):
            return NotImplemented
        self.extend(other)
        return self

    def __imul__(self: AbstractMutableSequence[T], n: int) -> AbstractMutableSequence[T]:
        """
        Concatenates the contents of this sequence n times in-place.

        :param n: The number of times to repeat the sequence.
        :type n: int

        :return: Self after concatenation.
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
