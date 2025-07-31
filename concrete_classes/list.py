from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Callable, TYPE_CHECKING, ClassVar

from abstract_classes.abstract_sequence import AbstractMutableSequence, AbstractSequence
from abstract_classes.collection import Collection
from abstract_classes.generic_base import class_name

if TYPE_CHECKING:
    from concrete_classes.dict import MutableDict, ImmutableDict
    from concrete_classes.set import MutableSet, ImmutableSet


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableList[T](AbstractMutableSequence[T]):
    """
    Concrete mutable implementation of AbstractMutableSequence, with a list as its underlying container.

    It adds some basic methods to transform the list into other classes created in this file: ImmutableList,
    MutableSet, ImmutableSet, MutableDict and ImmutableDict.
    """

    item_type: type[T]
    values: list[T]

    _comparable_types: ClassVar[type[Collection] | tuple[type[Collection], ...]] = AbstractSequence

    def __init__(
        self: MutableList[T],
        *values: Iterable[T] | Collection[T] | T,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        """
        Delegates to Collection's init propagating or fixing the configuration parameters.

        _coerce and _skip_validation are propagated, and _forbidden_iterable_types is set to contain AbstractSet, set
        and frozenset, as initializing a list with the values of a set can't guarantee a consistent ordering of them.

        The _finisher parameter of Collection's init is inferred from AbstractMutableSequence's ClassVar _finisher
        attribute, which is by default set to list.

        :param values: One or more values for the MutableList to contain.
        :type values: Iterable[T] | Collection[T] | T

        :param _coerce: State parameter that, if True, attempts to coerce the values to the type inferred from the generic.
        :type _coerce: bool

        :param _skip_validation: State parameter that, if True, skips the validation of the values.
        :type _skip_validation: bool
        """
        Collection.__init__(self, *values, _coerce=_coerce, _skip_validation=_skip_validation)

    def to_immutable_list(self: MutableList[T]) -> ImmutableList[T]:
        """
        Returns this list as an ImmutableList.

        :return: A new ImmutableList object with the same item_type as self and containing the same values on the same
        order. Validation is skipped when creating this object.
        :type: ImmutableList[T]
        """
        return ImmutableList[self.item_type](self.values, _skip_validation=True)

    def to_mutable_set(self: MutableList[T]) -> MutableSet[T]:
        """
        Returns this list as a MutableSet.

        :return: A new MutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: MutableSet[T]
        """
        from concrete_classes.set import MutableSet
        return MutableSet[self.item_type](self.values, _skip_validation=True)

    def to_immutable_set(self: MutableList[T]) -> ImmutableSet[T]:
        """
        Returns this list as an ImmutableSet.

        :return: A new ImmutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: ImmutableSet[T]
        """
        from concrete_classes.set import ImmutableSet
        return ImmutableSet[self.item_type](self.values, _skip_validation=True)

    def to_mutable_dict[K, V](
        self: MutableList[T],
        key_mapper: Callable[[T], K] = lambda x : x,
        value_mapper: Callable[[T], V] = lambda x : x
    ) -> MutableDict[K, V]:
        """
        Returns a MutableDict obtained by calling the key and value mappers on each item of the Collection.

        :param key_mapper: Function to obtain the keys from. Defaults to identity mapping.
        :type key_mapper: Callable[[T], K]

        :param value_mapper: Function to obtain the values from. Defaults to identity mapping.
        :type value_mapper: Callable[[T], V]

        :return: A new MutableDict object containing the (key, value) pairs obtained by applying the key and value
        mappings to the elements of this MutableList, inferring the dict types from them.
        :rtype: MutableDict[K, V]
        """
        from concrete_classes.dict import MutableDict
        return MutableDict.of(self.to_dict(key_mapper, value_mapper))

    def to_immutable_dict[K, V](
        self: MutableList[T],
        key_mapper: Callable[[T], K] = lambda x : x,
        value_mapper: Callable[[T], V] = lambda x : x
    ) -> ImmutableDict[K, V]:
        """
        Returns an ImmutableDict obtained by calling the key and value mappers on each item of the Collection.

        :param key_mapper: Function to obtain the keys from. Defaults to identity mapping.
        :type key_mapper: Callable[[T], K]

        :param value_mapper: Function to obtain the values from. Defaults to identity mapping.
        :type value_mapper: Callable[[T], V]

        :return: A new ImmutableDict object containing the (key, value) pairs obtained by applying the key and value
        mappings to the elements of this MutableList, inferring the dict types from them.
        :rtype: ImmutableDict[K, V]
        """
        from concrete_classes.dict import ImmutableDict
        return ImmutableDict.of(self.to_dict(key_mapper, value_mapper))


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ImmutableList[T](AbstractSequence[T]):
    """
    Concrete immutable implementation of AbstractSequence, with a tuple as its underlying container.

    It adds some basic methods to transform the list into other classes created in this file: MutableList,
    MutableSet, ImmutableSet, MutableDict and ImmutableDict.
    """

    item_type: type[T]
    values: tuple[T, ...]

    _comparable_types: ClassVar[type[Collection] | tuple[type[Collection], ...]] = AbstractSequence

    def __init__(
        self: ImmutableList[T],
        *values: Iterable[T] | Collection[T] | T,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        """
        Delegates to Collection's init propagating or fixing the configuration parameters.

        _coerce and _skip_validation are propagated, and _forbidden_iterable_types is set to contain AbstractSet, set
        and frozenset, as initializing a list with the values of a set can't guarantee a consistent ordering of them.

        The _finisher parameter of Collection's init is inferred from AbstractSequence's ClassVar _finisher attribute,
        which is by default set to tuple.

        :param values: One or more values for the MutableList to contain.
        :type values: Iterable[T] | Collection[T] | T

        :param _coerce: State parameter that, if True, attempts to coerce the values to the type inferred from the generic.
        :type _coerce: bool

        :param _skip_validation: State parameter that, if True, skips the validation of the values.
        :type _skip_validation: bool
        """
        Collection.__init__(self, *values, _coerce=_coerce, _skip_validation=_skip_validation)

    def __repr__(self: Collection[T]) -> str:
        return f"{class_name(type(self))}{list(self.values)}"

    def to_mutable_list(self: ImmutableList[T]) -> MutableList[T]:
        """
        Returns this list as a MutableList.

        :return: A new MutableList object with the same item_type as self and containing the same values on the same
        order. Validation is skipped when creating this object.
        :type: MutableList[T]
        """
        return MutableList[self.item_type](self.values, _skip_validation=True)

    def to_mutable_set(self: ImmutableList[T]) -> MutableSet[T]:
        """
        Returns this list as a MutableSet.

        :return: A new MutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: MutableSet[T]
        """
        from concrete_classes.set import MutableSet
        return MutableSet[self.item_type](self.values, _skip_validation=True)

    def to_immutable_set(self: ImmutableList[T]) -> ImmutableSet[T]:
        """
        Returns this list as an ImmutableSet.

        :return: A new ImmutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: ImmutableSet[T]
        """
        from concrete_classes.set import ImmutableSet
        return ImmutableSet[self.item_type](self.values, _skip_validation=True)

    def to_mutable_dict[K, V](
        self: ImmutableList[T],
        key_mapper: Callable[[T], K] = lambda x : x,
        value_mapper: Callable[[T], V] = lambda x : x
    ) -> MutableDict[K, V]:
        """
        Returns a MutableDict obtained by calling the key and value mappers on each item of the Collection.

        :param key_mapper: Function to obtain the keys from. Defaults to identity mapping.
        :type key_mapper: Callable[[T], K]

        :param value_mapper: Function to obtain the values from. Defaults to identity mapping.
        :type value_mapper: Callable[[T], V]

        :return: A new MutableDict object containing the (key, value) pairs obtained by applying the key and value
        mappings to the elements of this MutableList, inferring the dict types from them.
        :rtype: MutableDict[K, V]
        """
        from concrete_classes.dict import MutableDict
        return MutableDict.of(self.to_dict(key_mapper, value_mapper))

    def to_immutable_dict[K, V](
        self: ImmutableList[T],
        key_mapper: Callable[[T], K] = lambda x : x,
        value_mapper: Callable[[T], V] = lambda x : x
    ) -> ImmutableDict[K, V]:
        """
        Returns an ImmutableDict obtained by calling the key and value mappers on each item of the Collection.

        :param key_mapper: Function to obtain the keys from. Defaults to identity mapping.
        :type key_mapper: Callable[[T], K]

        :param value_mapper: Function to obtain the values from. Defaults to identity mapping.
        :type value_mapper: Callable[[T], V]

        :return: A new ImmutableDict object containing the (key, value) pairs obtained by applying the key and value
        mappings to the elements of this MutableList, inferring the dict types from them.
        :rtype: ImmutableDict[K, V]
        """
        from concrete_classes.dict import ImmutableDict
        return ImmutableDict.of(self.to_dict(key_mapper, value_mapper))
