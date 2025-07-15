from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Iterable, Mapping
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


@dataclass(frozen=True, slots=True, repr=False)
class MutableList(AbstractMutableSequence[T]):

    item_type: type[T]
    values: list[T]

    def __init__(
        self: MutableList[T],
        item_type: type[T] | None = None,
        values: Iterable[T] | Collection[T] | None = None,
        coerce: bool = False
    ) -> None:
        Collection.__init__(self, item_type, values, (AbstractSet, set, frozenset), coerce=coerce)

    def to_immutable_list(self: MutableList[T]) -> ImmutableList[T]:
        return ImmutableList(self.item_type, self.values)

    def to_mutable_set(self: MutableList[T]) -> MutableSet[T]:
        return MutableSet(self.item_type, self.values)

    def to_immutable_set(self: MutableList[T]) -> ImmutableSet[T]:
        return ImmutableSet(self.item_type, self.values)


@dataclass(frozen=True, slots=True, repr=False)
class ImmutableList(AbstractSequence[T]):

    item_type: type[T]
    values: tuple[T, ...]

    def __init__(
        self: ImmutableList[T],
        item_type: type[T] | None = None,
        values: Iterable[T] | Collection[T] | None = None,
        coerce: bool = False
    ) -> None:
        Collection.__init__(self, item_type, values, (AbstractSet, set, frozenset), coerce=coerce, finisher=tuple)

    def __repr__(self: Collection[T]) -> str:
        return f"{class_name(self)}<{self.item_type.__name__}>{list(self.values)}"

    def to_mutable_list(self: ImmutableList[T]) -> MutableList[T]:
        return MutableList(self.item_type, self.values)

    def to_mutable_set(self: ImmutableList[T]) -> MutableSet[T]:
        return MutableSet(self.item_type, self.values)

    def to_immutable_set(self: ImmutableList[T]) -> ImmutableSet[T]:
        return ImmutableSet(self.item_type, self.values)


@dataclass(frozen=True, slots=True, repr=False)
class MutableDict(AbstractMutableDict[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    def __init__(
        self: MutableDict[K, V],
        key_type: type[K],
        value_type: type[V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        coerce_keys: bool = False,
        coerce_values: bool = False
    ) -> None:
        AbstractDict.__init__(self, key_type, value_type, keys_values, coerce_keys=coerce_keys,
                              coerce_values=coerce_values)

    def to_immutable_dict(self: MutableDict[K, V]) -> ImmutableDict[K, V]:
        return ImmutableDict(self.key_type, self.value_type, self)


@dataclass(frozen=True, slots=True, repr=False)
class ImmutableDict(AbstractDict[K, V]):

    key_type: type[K]
    value_type: type[V]
    data: immutabledict[K, V]

    def __init__(
        self: MutableDict[K, V],
        key_type: type[K],
        value_type: type[V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        coerce_keys: bool = False,
        coerce_values: bool = False
    ) -> None:
        AbstractDict.__init__(self, key_type, value_type, keys_values, coerce_keys=coerce_keys,
                              coerce_values=coerce_values, finisher=immutabledict)

    def to_mutable_dict(self: ImmutableDict[K, V]) -> MutableDict[K, V]:
        return MutableDict(self.key_type, self.value_type, self)


@dataclass(frozen=True, slots=True, repr=False)
class MutableSet(AbstractMutableSet[T]):

    item_type: type[T]
    values: set[T]

    def __init__(
        self: MutableSet[T],
        item_type: type[T] | None = None,
        values: Iterable[T] | Collection[T] | None = None,
        coerce: bool = False
    ) -> None:
        Collection.__init__(self, item_type, values, coerce=coerce, finisher=set)

    def to_immutable_set(self: MutableSet[T]) -> ImmutableSet[T]:
        return ImmutableSet(self.item_type, self)


@dataclass(frozen=True, slots=True, repr=False)
class ImmutableSet(AbstractSet[T]):

    item_type: type[T]
    values: frozenset[T]

    def __init__(
        self: ImmutableSet[T],
        item_type: type[T] | None = None,
        values: Iterable[T] | Collection[T] | None = None,
        coerce: bool = False
    ) -> None:
        Collection.__init__(self, item_type, values, coerce=coerce, finisher=frozenset)

    def __repr__(self: Collection[T]) -> str:
        return f"{class_name(self)}<{self.item_type.__name__}>{set(self.values)}"

    def to_mutable_set(self: ImmutableSet[T]) -> MutableSet[T]:
        return MutableSet(self.item_type, self)
