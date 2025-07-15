from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Callable, TypeVar, TYPE_CHECKING

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True, slots=True, repr=False)
class Maybe(Generic[T]):

    item_type: type[T]
    value: T | None

    def __init__(self: Maybe[T], value: T | None = None, item_type: type[T] | None = None, coerce: bool = False) -> None:
        from type_validation import _validate_or_coerce_value

        if value is not None and item_type is not None:
            object.__setattr__(self, 'item_type', item_type)
            object.__setattr__(self, 'value', _validate_or_coerce_value(item_type, value, coerce))
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
        return Maybe(None, item_type)

    @staticmethod
    def of(value: T, item_type: type[T] | None = None) -> Maybe[T]:
        if value is None:
            raise ValueError("Can't create a Maybe.of with a None value.")
        return Maybe(value, item_type)

    @staticmethod
    def of_nullable(value: T | None, item_type: type[T]) -> Maybe[T]:
        return Maybe(value, item_type)

    def is_present(self: Maybe[T]) -> bool:
        return self.value is not None

    def is_empty(self: Maybe[T]) -> bool:
        return self.value is None

    def get(self: Maybe[T]) -> T:
        if self.is_empty():
            raise ValueError("No value present")
        return self.value

    def or_else(
        self: Maybe[T],
        fallback: T,
        coerce: bool = False
    ) -> T:
        if coerce:
            from type_validation import _validate_or_coerce_value
            fallback = _validate_or_coerce_value(self.item_type, fallback, coerce)
        if not isinstance(fallback, self.item_type):
            raise TypeError(f"Fallback value {fallback} is not of type {self.item_type.__name__}, but of {type(fallback).__name__}")
        return self.value if self.is_present() else fallback

    def or_else_get(
        self: Maybe[T],
        supplier: Callable[[], T],
        coerce: bool = False
    ) -> T:
        supplied_value = supplier()
        if coerce:
            from type_validation import _validate_or_coerce_value
            supplied_value = _validate_or_coerce_value(self.item_type, supplied_value, coerce)
        if not isinstance(supplied_value, self.item_type):
            raise TypeError(f"Supplied value {supplied_value} is not of type {self.item_type.__name__}, but of {type(supplied_value).__name__}")
        return self.value if self.is_present() else supplied_value

    def or_else_raise(self: Maybe[T], exception_supplier: Callable[[], Exception]) -> T:
        if self.is_present():
            return self.value
        raise exception_supplier()

    def if_present(self: Maybe[T], consumer: Callable[[T], None]) -> None:
        if self.is_present():
            consumer(self.value)

    def map(self: Maybe[T], f: Callable[[T], U]) -> Maybe[U]:
        if self.value is None:
            raise ValueError("There's no value to apply the function to.")
        result = f(self.value)
        if result is None:
            raise ValueError("Callable function returned a None value.")
        return Maybe.of(result)

    def map_or_else(
        self: Maybe[T],
        f: Callable[[T], U],
        fallback: U,
        coerce: bool = False
    ) -> U:
        if coerce:
            from type_validation import _validate_or_coerce_value
            fallback = _validate_or_coerce_value(self.item_type, fallback, coerce)
        return f(self.value) if self.is_present() else fallback

    def flatmap(
        self: Maybe[T],
        f: Callable[[T], Maybe[U]]
    ) -> Maybe[U]:
        if self.is_empty():
            raise ValueError("There's no value to apply the function to.")
        result = f(self.value)
        if not isinstance(result, Maybe):
            raise TypeError("flatmap mapper must return a Maybe object.")
        if result.is_empty():
            raise ValueError("flatmap mapper returned an empty value.")
        return result.get()

    def filter(
        self: Maybe[T],
        predicate: Callable[[T], bool]
    ) -> Maybe[T]:
        return self if self.is_present() and predicate(self.value) else Maybe.empty(self.item_type)

    def __bool__(self: Maybe[T]) -> bool:
        return bool(self.value)

    def __repr__(self: Maybe[T]) -> str:
        from abstract_classes import class_name
        cls_name: str = class_name(self)
        return f"{cls_name}.of({self.value!r})" if self.is_present() else f"{cls_name}.empty({self.item_type.__name__})"
