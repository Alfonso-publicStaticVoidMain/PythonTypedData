from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, get_args, Callable
from immutabledict import immutabledict

from abstract_classes import (
    Collection,
    AbstractSequence, AbstractMutableSequence,
    AbstractSet, AbstractMutableSet,
    AbstractDict, AbstractMutableDict,
    class_name
)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableList[T](AbstractMutableSequence[T]):
    """
    Concrete mutable implementation of AbstractMutableSequence, with a list as its underlying container.

    It adds some basic methods to transform the list into other classes created in this file: ImmutableList,
    MutableSet, ImmutableSet, MutableDict and ImmutableDict.
    """

    item_type: type[T]
    values: list[T]

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
        Collection.__init__(self, *values, _forbidden_iterable_types=(AbstractSet, set, frozenset), _coerce=_coerce, _skip_validation=_skip_validation)

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
        return MutableSet[self.item_type](self.values, _skip_validation=True)

    def to_immutable_set(self: MutableList[T]) -> ImmutableSet[T]:
        """
        Returns this list as an ImmutableSet.

        :return: A new ImmutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: ImmutableSet[T]
        """
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
        Collection.__init__(self, *values, _forbidden_iterable_types=(AbstractSet, set, frozenset), _coerce=_coerce, _skip_validation=_skip_validation)

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
        return MutableSet[self.item_type](self.values, _skip_validation=True)

    def to_immutable_set(self: ImmutableList[T]) -> ImmutableSet[T]:
        """
        Returns this list as an ImmutableSet.

        :return: A new ImmutableSet object with the same item_type as self and containing the same values. Validation is
        skipped when creating this object.
        :type: ImmutableSet[T]
        """
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
        return ImmutableDict.of(self.to_dict(key_mapper, value_mapper))


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableSet[T](AbstractMutableSet[T]):
    """
    Concrete mutable implementation of AbstractMutableSet, with a set as its underlying container.

    It adds some basic methods to transform the set into other classes created in this file: ImmutableSet, MutableDict
    and ImmutableDict.
    """

    item_type: type[T]
    values: set[T]

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


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableDict[K, V](AbstractMutableDict[K, V]):
    """
    Concrete mutable implementation of AbstractMutableDict, with a dict as its underlying container.

    It adds some basic methods to transform the dict, its keys or values into other classes created in this file:
    MutableList, ImmutableList, MutableSet, ImmutableSet and ImmutableDict.
    """

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __init__(
        self: MutableDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        _coerce_keys: bool = False,
        _coerce_values: bool = False,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None,
        _skip_validation: bool = False
    ) -> None:
        AbstractDict.__init__(self, keys_values, _coerce_keys=_coerce_keys, _coerce_values=_coerce_values, _keys=_keys, _values=_values, _skip_validation=_skip_validation)

    def to_immutable_dict(self: MutableDict[K, V]) -> ImmutableDict[K, V]:
        """
        Returns this dict as an ImmutableDict.

        :return: A new ImmutableDict object with the same key and value types as self and containing the data.
        Validation is skipped when creating this object.
        :type: ImmutableDict[T]
        """
        return ImmutableDict[self.key_type, self.value_type](self.data, _skip_validation=True)

    def keys_as_mutable_list(self: MutableDict[K, V]) -> MutableList[K]:
        """
        Returns a MutableList containing all keys in the dictionary.

        :return: A MutableList of keys.
        :rtype: MutableList[K]
        """
        return MutableList[self.key_type](self.keys())

    def keys_as_immutable_list(self: MutableDict[K, V]) -> ImmutableList[K]:
        """
        Returns an ImmutableList containing all keys in the dictionary.

        :return: A new ImmutableList object with the key type as its item type containing all the keys.
        :rtype: ImmutableList[K]
        """
        return ImmutableList[self.key_type](self.keys())

    def keys_as_mutable_set(self: MutableDict[K, V]) -> MutableSet[K]:
        """
        Returns a MutableSet containing all keys in the dictionary.

        :return: A new MutableSet object with the key type as its item type containing all the keys.
        :rtype: MutableSet[K]
        """
        return MutableSet[self.key_type](self.keys())

    def keys_as_immutable_set(self: MutableDict[K, V]) -> ImmutableSet[K]:
        """
        Returns an ImmutableSet containing all keys in the dictionary.

        :return: A new ImmutableSet object with the key type as its item type containing all the keys.
        :rtype: ImmutableSet[K]
        """
        return ImmutableSet[self.key_type](self.keys())

    def values_as_mutable_list(self: MutableDict[K, V]) -> MutableList[V]:
        """
        Returns a MutableList containing all values in the dictionary.

        :return: A new MutableList object with the value type as its item type containing all the values.
        :rtype: MutableList[V]
        """
        return MutableList[self.value_type](self.values())

    def values_as_immutable_list(self: MutableDict[K, V]) -> ImmutableList[V]:
        """
        Returns an ImmutableList containing all values in the dictionary.

        :return: A new ImmutableList object with the value type as its item type containing all the values.
        :rtype: ImmutableList[V]
        """
        return ImmutableList[self.value_type](self.values())

    def values_as_mutable_set(self: MutableDict[K, V]) -> MutableSet[V]:
        """
        Returns a MutableSet containing all unique values in the dictionary.

        :return: A new MutableSet object with the value type as its item type containing all the values.
        :rtype: MutableSet[V]
        """
        return MutableSet[self.value_type](self.values())

    def values_as_immutable_set(self: MutableDict[K, V]) -> ImmutableSet[V]:
        """
        Returns an ImmutableSet containing all unique values in the dictionary.

        :return: A new ImmutableSet object with the value type as its item type containing all the values.
        :rtype: ImmutableSet[V]
        """
        return ImmutableSet[self.value_type](self.values())


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ImmutableDict[K, V](AbstractDict[K, V]):
    """
    Concrete immutable implementation of AbstractDict, with an immutabledict as its underlying container.

    It adds some basic methods to transform the dict, its keys or values into other classes created in this file:
    MutableList, ImmutableList, MutableSet, ImmutableSet and MutableDict.
    """

    key_type: type[K]
    value_type: type[V]
    data: immutabledict[K, V]

    def __init__(
        self: ImmutableDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        _coerce_keys: bool = False,
        _coerce_values: bool = False,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None,
        _skip_validation: bool = False
    ) -> None:
        AbstractDict.__init__(self, keys_values, _coerce_keys=_coerce_keys, _coerce_values=_coerce_values, _keys=_keys, _values=_values, _skip_validation=_skip_validation)

    def to_mutable_dict(self: ImmutableDict[K, V]) -> MutableDict[K, V]:
        return MutableDict[self.key_type, self.value_type](self.data, _skip_validation=True)

    def to_mutable_dict(self: ImmutableDict[K, V]) -> MutableDict[K, V]:
        return MutableDict[self.key_type, self.value_type](self.data, _skip_validation=True)

    def keys_as_mutable_list(self: ImmutableDict[K, V]) -> MutableList[K]:
        """
        Returns a MutableList containing all keys in the dictionary.

        :return: A new MutableList object with the key type as its item type containing all the keys.
        :rtype: MutableList[K]
        """
        return MutableList[self.key_type](self.keys())

    def keys_as_immutable_list(self: ImmutableDict[K, V]) -> ImmutableList[K]:
        """
        Returns an ImmutableList containing all keys in the dictionary.

        :return: A new ImmutableList object with the key type as its item type containing all the keys.
        :rtype: ImmutableList[K]
        """
        return ImmutableList[self.key_type](self.keys())

    def keys_as_mutable_set(self: ImmutableDict[K, V]) -> MutableSet[K]:
        """
        Returns a MutableSet containing all keys in the dictionary.

        :return: A new MutableSet object with the key type as its item type containing all the keys.
        :rtype: MutableSet[K]
        """
        return MutableSet[self.key_type](self.keys())

    def keys_as_immutable_set(self: ImmutableDict[K, V]) -> ImmutableSet[K]:
        """
        Returns an ImmutableSet containing all keys in the dictionary.

        :return: A new ImmutableSet object with the key type as its item type containing all the keys.
        :rtype: ImmutableSet[K]
        """
        return ImmutableSet[self.key_type](self.keys())

    def values_as_mutable_list(self: ImmutableDict[K, V]) -> MutableList[V]:
        """
        Returns a MutableList containing all values in the dictionary.

        :return: A new MutableList object with the value type as its item type containing all the values.
        :rtype: MutableList[V]
        """
        return MutableList[self.value_type](self.values())

    def values_as_immutable_list(self: ImmutableDict[K, V]) -> ImmutableList[V]:
        """
        Returns an ImmutableList containing all values in the dictionary.

        :return: A new ImmutableList object with the value type as its item type containing all the values.
        :rtype: ImmutableList[V]
        """
        return ImmutableList[self.value_type](self.values())

    def values_as_mutable_set(self: ImmutableDict[K, V]) -> MutableSet[V]:
        """
        Returns a MutableSet containing all unique values in the dictionary.

        :return: A new MutableSet object with the value type as its item type containing all the values.
        :rtype: MutableSet[V]
        """
        return MutableSet[self.value_type](self.values())

    def values_as_immutable_set(self: ImmutableDict[K, V]) -> ImmutableSet[V]:
        """
        Returns an ImmutableSet containing all unique values in the dictionary.

        :return: A new ImmutableSet object with the value type as its item type containing all the values.
        :rtype: ImmutableSet[V]
        """
        return ImmutableSet[self.value_type](self.values())
