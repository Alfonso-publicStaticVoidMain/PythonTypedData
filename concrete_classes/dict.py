from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Iterable, TYPE_CHECKING

from immutabledict import immutabledict

from abstract_classes.abstract_dict import AbstractMutableDict, AbstractDict
if TYPE_CHECKING:
    from concrete_classes.list import MutableList, ImmutableList
    from concrete_classes.set import MutableSet, ImmutableSet


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
        from concrete_classes.list import MutableList
        return MutableList[self.key_type](self.keys())

    def keys_as_immutable_list(self: MutableDict[K, V]) -> ImmutableList[K]:
        """
        Returns an ImmutableList containing all keys in the dictionary.

        :return: A new ImmutableList object with the key type as its item type containing all the keys.
        :rtype: ImmutableList[K]
        """
        from concrete_classes.list import ImmutableList
        return ImmutableList[self.key_type](self.keys())

    def keys_as_mutable_set(self: MutableDict[K, V]) -> MutableSet[K]:
        """
        Returns a MutableSet containing all keys in the dictionary.

        :return: A new MutableSet object with the key type as its item type containing all the keys.
        :rtype: MutableSet[K]
        """
        from concrete_classes.set import MutableSet
        return MutableSet[self.key_type](self.keys())

    def keys_as_immutable_set(self: MutableDict[K, V]) -> ImmutableSet[K]:
        """
        Returns an ImmutableSet containing all keys in the dictionary.

        :return: A new ImmutableSet object with the key type as its item type containing all the keys.
        :rtype: ImmutableSet[K]
        """
        from concrete_classes.set import ImmutableSet
        return ImmutableSet[self.key_type](self.keys())

    def values_as_mutable_list(self: MutableDict[K, V]) -> MutableList[V]:
        """
        Returns a MutableList containing all values in the dictionary.

        :return: A new MutableList object with the value type as its item type containing all the values.
        :rtype: MutableList[V]
        """
        from concrete_classes.list import MutableList
        return MutableList[self.value_type](self.values())

    def values_as_immutable_list(self: MutableDict[K, V]) -> ImmutableList[V]:
        """
        Returns an ImmutableList containing all values in the dictionary.

        :return: A new ImmutableList object with the value type as its item type containing all the values.
        :rtype: ImmutableList[V]
        """
        from concrete_classes.list import ImmutableList
        return ImmutableList[self.value_type](self.values())

    def values_as_mutable_set(self: MutableDict[K, V]) -> MutableSet[V]:
        """
        Returns a MutableSet containing all unique values in the dictionary.

        :return: A new MutableSet object with the value type as its item type containing all the values.
        :rtype: MutableSet[V]
        """
        from concrete_classes.set import MutableSet
        return MutableSet[self.value_type](self.values())

    def values_as_immutable_set(self: MutableDict[K, V]) -> ImmutableSet[V]:
        """
        Returns an ImmutableSet containing all unique values in the dictionary.

        :return: A new ImmutableSet object with the value type as its item type containing all the values.
        :rtype: ImmutableSet[V]
        """
        from concrete_classes.set import ImmutableSet
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

    def to_immutable_dict(self: ImmutableDict[K, V]) -> MutableDict[K, V]:
        return MutableDict[self.key_type, self.value_type](self.data, _skip_validation=True)

    def keys_as_mutable_list(self: ImmutableDict[K, V]) -> MutableList[K]:
        """
        Returns a MutableList containing all keys in the dictionary.

        :return: A new MutableList object with the key type as its item type containing all the keys.
        :rtype: MutableList[K]
        """
        from concrete_classes.list import MutableList
        return MutableList[self.key_type](self.keys())

    def keys_as_immutable_list(self: ImmutableDict[K, V]) -> ImmutableList[K]:
        """
        Returns an ImmutableList containing all keys in the dictionary.

        :return: A new ImmutableList object with the key type as its item type containing all the keys.
        :rtype: ImmutableList[K]
        """
        from concrete_classes.list import ImmutableList
        return ImmutableList[self.key_type](self.keys())

    def keys_as_mutable_set(self: ImmutableDict[K, V]) -> MutableSet[K]:
        """
        Returns a MutableSet containing all keys in the dictionary.

        :return: A new MutableSet object with the key type as its item type containing all the keys.
        :rtype: MutableSet[K]
        """
        from concrete_classes.set import MutableSet
        return MutableSet[self.key_type](self.keys())

    def keys_as_immutable_set(self: ImmutableDict[K, V]) -> ImmutableSet[K]:
        """
        Returns an ImmutableSet containing all keys in the dictionary.

        :return: A new ImmutableSet object with the key type as its item type containing all the keys.
        :rtype: ImmutableSet[K]
        """
        from concrete_classes.set import ImmutableSet
        return ImmutableSet[self.key_type](self.keys())

    def values_as_mutable_list(self: ImmutableDict[K, V]) -> MutableList[V]:
        """
        Returns a MutableList containing all values in the dictionary.

        :return: A new MutableList object with the value type as its item type containing all the values.
        :rtype: MutableList[V]
        """
        from concrete_classes.list import MutableList
        return MutableList[self.value_type](self.values())

    def values_as_immutable_list(self: ImmutableDict[K, V]) -> ImmutableList[V]:
        """
        Returns an ImmutableList containing all values in the dictionary.

        :return: A new ImmutableList object with the value type as its item type containing all the values.
        :rtype: ImmutableList[V]
        """
        from concrete_classes.list import ImmutableList
        return ImmutableList[self.value_type](self.values())

    def values_as_mutable_set(self: ImmutableDict[K, V]) -> MutableSet[V]:
        """
        Returns a MutableSet containing all unique values in the dictionary.

        :return: A new MutableSet object with the value type as its item type containing all the values.
        :rtype: MutableSet[V]
        """
        from concrete_classes.set import MutableSet
        return MutableSet[self.value_type](self.values())

    def values_as_immutable_set(self: ImmutableDict[K, V]) -> ImmutableSet[V]:
        """
        Returns an ImmutableSet containing all unique values in the dictionary.

        :return: A new ImmutableSet object with the value type as its item type containing all the values.
        :rtype: ImmutableSet[V]
        """
        from concrete_classes.set import ImmutableSet
        return ImmutableSet[self.value_type](self.values())
