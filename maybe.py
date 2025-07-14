from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Callable, TypeVar, TYPE_CHECKING

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True, slots=True, repr=False)
class Maybe(Generic[T]):

    item_type: type[T]
    value: T | None

    def __init__(
        self: Maybe[T],
        item_type: type[T] | None = None,
        value: T | None = None
    ) -> None:
        from type_validation import _validate_or_coerce_value

        if value is not None and item_type is not None:
            object.__setattr__(self, 'item_type', item_type)
            object.__setattr__(self, 'value', _validate_or_coerce_value(item_type, value))
        elif value is not None and item_type is None:
            object.__setattr__(self, 'item_type', type(value))
            object.__setattr__(self, 'value', value)
        elif value is None and item_type is None:
            raise TypeError(f"You must provide either a type or a value.")
        else:
            object.__setattr__(self, 'item_type', item_type)
            object.__setattr__(self, 'value', None)

    @staticmethod
    def empty(item_type: type[T]) -> Maybe[T]:
        return Maybe(item_type, None)

    @staticmethod
    def of(value: T) -> Maybe[T]:
        if value is None:
            raise ValueError("Cannot create StaticOptional.of with None")
        return Maybe(type(value), value)

    @staticmethod
    def of_nullable(value: T | None, item_type: type[T]) -> Maybe[T]:
        if value is None:
            return Maybe.empty(item_type)
        return Maybe(item_type, value)

    def is_present(self: Maybe[T]) -> bool:
        return self.value is not None

    def is_empty(self: Maybe[T]) -> bool:
        return self.value is None

    def get(self: Maybe[T]) -> T:
        if self.is_empty():
            raise ValueError("No value present")
        return self.value

    def or_else(self: Maybe[T], fallback: T) -> T:
        return self.value or fallback

    def or_else_get(self: Maybe[T], supplier: Callable[[], T]) -> T:
        return self.value or supplier()

    def or_else_raise(self: Maybe[T], exception_supplier: Callable[[], Exception]) -> T:
        if self.is_present():
            return self.value
        raise exception_supplier()

    def if_present(self: Maybe[T], consumer: Callable[[T], None]) -> None:
        if self.is_present():
            consumer(self.value)

    def map(self: Maybe[T], f: Callable[[T], U]) -> Maybe[U]:
        if self.value is None:
            return Maybe.empty(object)
        result = f(self.value)
        if result is None:
            return Maybe.empty(object)
        return Maybe.of(result)

    def map_or_else(self, f: Callable[[T], U], fallback: U) -> U:
        if self.is_present():
            return f(self.value)
        else:
            return fallback

    def flatmap(self: Maybe[T], f: Callable[[T], Maybe[U]]) -> Maybe[U]:
        if self.is_empty():
            return Maybe.empty(self.item_type)
        result = f(self.value)
        if not isinstance(result, Maybe):
            raise TypeError("flatmap mapper must return StaticOptional")
        return result

    def filter(self: Maybe[T], predicate: Callable[[T], bool]) -> Maybe[T]:
        if self.is_empty() or not predicate(self.value):
            return Maybe.empty(self.item_type)
        return self

    def __bool__(self: Maybe[T]) -> bool:
        return bool(self.value) if self.is_present() else False

    def __repr__(self: Maybe[T]) -> str:
        from abstract_classes import class_name
        cls_name: str = class_name(self)
        return f"{cls_name}.of({self.value!r})" if self.is_present() else f"{cls_name}.empty({self.item_type.__name__})"
