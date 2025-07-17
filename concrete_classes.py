from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Iterable, Mapping, get_args
from immutabledict import immutabledict

from abstract_classes import (
    Collection,
    AbstractSequence, AbstractMutableSequence,
    AbstractSet, AbstractMutableSet,
    AbstractDict, AbstractMutableDict,
    class_name
)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
U = TypeVar("U")


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableList[T](AbstractMutableSequence[T]):

    item_type: type[T]
    values: list[T]

    def __init__(
        self: MutableList[T],
        values: Iterable[T] | Collection[T] | None = None,
        *,
        coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        Collection.__init__(self, values, _forbidden_iterable_types=(AbstractSet, set, frozenset), coerce=coerce, _skip_validation=_skip_validation)

    def to_immutable_list(self: MutableList[T]) -> ImmutableList[T]:
        return ImmutableList(self.values, self.item_type, _skip_validation=True)

    def to_mutable_set(self: MutableList[T]) -> MutableSet[T]:
        return MutableSet(self.values, self.item_type, _skip_validation=True)

    def to_immutable_set(self: MutableList[T]) -> ImmutableSet[T]:
        return ImmutableSet(self.values, self.item_type, _skip_validation=True)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ImmutableList[T](AbstractSequence[T]):

    item_type: type[T]
    values: tuple[T, ...]

    def __init__(
        self: ImmutableList[T],
        values: Iterable[T] | Collection[T] | None = None,
        *,
        coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        Collection.__init__(self, values, _forbidden_iterable_types=(AbstractSet, set, frozenset), coerce=coerce, _finisher=tuple, _skip_validation=_skip_validation)

    def __repr__(self: Collection[T]) -> str:
        return f"{class_name(self)}<{self.item_type.__name__}>{list(self.values)}"

    def to_mutable_list(self: ImmutableList[T]) -> MutableList[T]:
        return MutableList(self.values, self.item_type, _skip_validation=True)

    def to_mutable_set(self: ImmutableList[T]) -> MutableSet[T]:
        return MutableSet(self.values, self.item_type, _skip_validation=True)

    def to_immutable_set(self: ImmutableList[T]) -> ImmutableSet[T]:
        return ImmutableSet(self.values, self.item_type, _skip_validation=True)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableSet[T](AbstractMutableSet[T]):

    item_type: type[T]
    values: set[T]

    def __init__(
        self: MutableSet[T],
        values: Iterable[T] | Collection[T] | None = None,
        *,
        coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        Collection.__init__(self, values, coerce=coerce, _finisher=set, _skip_validation=_skip_validation)

    def to_immutable_set(self: MutableSet[T]) -> ImmutableSet[T]:
        return ImmutableSet[self.item_type](self.values, _skip_validation=True)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ImmutableSet[T](AbstractSet[T]):

    item_type: type[T]
    values: frozenset[T]

    def __init__(
        self: ImmutableSet[T],
        values: Iterable[T] | Collection[T] | None = None,
        *,
        coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        Collection.__init__(self, values, coerce=coerce, _finisher=frozenset, _skip_validation=_skip_validation)

    def __repr__(self: Collection[T]) -> str:
        return f"{class_name(self)}<{self.item_type.__name__}>{set(self.values)}"

    def to_mutable_set(self: ImmutableSet[T]) -> MutableSet[T]:
        return MutableSet[self.item_type](self.values, _skip_validation=True)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class MutableDict[K, V](AbstractMutableDict[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __init__(
        self: MutableDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        coerce_keys: bool = False,
        coerce_values: bool = False,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None
    ) -> None:
        AbstractDict.__init__(self, keys_values, coerce_keys=coerce_keys, coerce_values=coerce_values, _keys=_keys, _values=_values)

    def to_immutable_dict(self: MutableDict[K, V]) -> ImmutableDict[K, V]:
        return ImmutableDict[self.key_type, self.value_type](self.data)


@dataclass(frozen=True, slots=True, repr=False, eq=False)
class ImmutableDict[K, V](AbstractDict[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: immutabledict[K, V]

    def __init__(
        self: ImmutableDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        coerce_keys: bool = False,
        coerce_values: bool = False,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None
    ) -> None:
        AbstractDict.__init__(self, keys_values, coerce_keys=coerce_keys, coerce_values=coerce_values, _finisher=immutabledict, _keys=_keys, _values=_values)

    def to_mutable_dict(self: ImmutableDict[K, V]) -> MutableDict[K, V]:
        return MutableDict[self.key_type, self.value_type](self.data)