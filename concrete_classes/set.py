from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Callable, ClassVar

from abstract_classes.abstract_set import AbstractMutableSet, AbstractSet
from abstract_classes.collection import Collection
from concrete_classes.dict import MutableDict, ImmutableDict


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableSet[T](AbstractMutableSet[T]):
    """
    Concrete mutable implementation of AbstractMutableSet, with a set as its underlying container.

    It adds some basic methods to transform the set into other classes created in this file: ImmutableSet, MutableDict
    and ImmutableDict.
    """

    item_type: type[T]
    values: set[T]

    _comparable_types: ClassVar[type[Collection] | tuple[type[Collection], ...]] = AbstractSet

    def __init__(
        self: MutableSet[T],
        *values: Iterable[T] | Collection[T] | T,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        """
        Delegates to Collection's init propagating or fixing the configuration parameters.

        _coerce and _skip_validation are propagated, and _forbidden_iterable_types is omitted, so it is empty by default.

        The _finisher parameter of Collection's init is inferred from AbstractMutableSet's ClassVar _finisher attribute,
        which is by default set to set.

        :param values: One or more values for the MutableList to contain.
        :type values: Iterable[T] | Collection[T] | T

        :param _coerce: State parameter that, if True, attempts to coerce the values to the type inferred from the generic.
        :type _coerce: bool

        :param _skip_validation: State parameter that, if True, skips the validation of the values.
        :type _skip_validation: bool
        """
        Collection.__init__(self, *values, _coerce=_coerce, _skip_validation=_skip_validation)

    def to_immutable_set(self: MutableSet[T]) -> ImmutableSet[T]:
        """
        Returns this set as an ImmutableSet.

        :return: A new ImmutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: ImmutableSet[T]
        """
        return ImmutableSet[self.item_type](self.values, _skip_validation=True)

    def to_mutable_dict[K, V](
        self: MutableSet[T],
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
        return MutableDict.of(self.to_dict(key_mapper, value_mapper))

    def to_immutable_dict[K, V](
        self: MutableSet[T],
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
        return ImmutableDict.of(self.to_dict(key_mapper, value_mapper))


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ImmutableSet[T](AbstractSet[T]):
    """
    Concrete immutable implementation of AbstractSet, with a frozenset as its underlying container.

    It adds some basic methods to transform the set into other classes created in this file: MutableSet, MutableDict
    and ImmutableDict.
    """

    item_type: type[T]
    values: frozenset[T]

    _comparable_types: ClassVar[type[Collection] | tuple[type[Collection], ...]] = AbstractSet

    def __init__(
        self: ImmutableSet[T],
        *values: Iterable[T] | Collection[T] | T,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        """
        Delegates to Collection's init propagating or fixing the configuration parameters.

        _coerce and _skip_validation are propagated, and _forbidden_iterable_types is omitted, so it is empty by default.

        The _finisher parameter of Collection's init is inferred from AbstractSet's ClassVar _finisher attribute, which
        is by default set to frozenset.

        :param values: One or more values for the MutableList to contain.
        :type values: Iterable[T] | Collection[T] | T

        :param _coerce: State parameter that, if True, attempts to coerce the values to the type inferred from the generic.
        :type _coerce: bool

        :param _skip_validation: State parameter that, if True, skips the validation of the values.
        :type _skip_validation: bool
        """
        Collection.__init__(self, *values, _coerce=_coerce, _skip_validation=_skip_validation)

    def __repr__(self: Collection[T]) -> str:
        return f"{type(self).__name__}{set(self.values)}"

    def to_mutable_set(self: ImmutableSet[T]) -> MutableSet[T]:
        """
        Returns this set as a MutableSet.

        :return: A new MutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: MutableSet[T]
        """
        return MutableSet[self.item_type](self.values, _skip_validation=True)

    def to_mutable_dict[K, V](
        self: ImmutableSet[T],
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
        return MutableDict.of(self.to_dict(key_mapper, value_mapper))

    def to_immutable_dict[K, V](
        self: ImmutableSet[T],
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
        return ImmutableDict.of(self.to_dict(key_mapper, value_mapper))
