from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Callable, get_args, ClassVar, Any
from weakref import WeakValueDictionary

from GenericBase import GenericBase


@dataclass(frozen=True, slots=True, repr=False)
class Maybe[T](GenericBase[T]):

    item_type: type[T]
    value: T | None

    def __init__(
        self: Maybe[T],
        value: T | None = None,
        *,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value

        generic_item_type = type(self)._inferred_item_type()

        actual_value = value if _skip_validation else _validate_or_coerce_value(value, generic_item_type, _coerce=_coerce) if value is not None else None

        object.__setattr__(self, 'item_type', generic_item_type)
        object.__setattr__(self, 'value', actual_value)

    @classmethod
    def _inferred_item_type(cls: Maybe[T]) -> type[T] | None:
        try:
            return cls._inferred_generic_args[0]
        except (AttributeError, IndexError, TypeError, KeyError):
            return None

    @classmethod
    def empty(cls, item_type: type[T]) -> Maybe[T]:
        return Maybe[item_type](None)

    @classmethod
    def of(cls, value: T) -> Maybe[T]:
        if value is None:
            raise ValueError("Can't use Maybe.of with a None obj.")
        from type_validation import _infer_type
        return Maybe[_infer_type(value)](value)

    @classmethod
    def of_nullable(cls, value: T | None, item_type: type[T]) -> Maybe[T]:
        if item_type is None:
            raise ValueError("You must give a type when using Maybe.of_nullable")
        from type_validation import _validate_or_coerce_value
        return Maybe[item_type](_validate_or_coerce_value(value, item_type)) if value is not None else Maybe[item_type]()

    def is_present(self: Maybe[T]) -> bool:
        return self.value is not None

    def is_empty(self: Maybe[T]) -> bool:
        return self.value is None

    def get(self: Maybe[T]) -> T:
        if self.is_empty():
            raise ValueError("No obj present")
        return self.value

    def or_else(
        self: Maybe[T],
        fallback: T,
        *,
        _coerce: bool = False
    ) -> T:
        if _coerce:
            from type_validation import _validate_or_coerce_value
            fallback = _validate_or_coerce_value(fallback, self.item_type, _coerce=_coerce)
        if not isinstance(fallback, self.item_type):
            raise TypeError(f"Fallback obj {fallback} is not of type {self.item_type.__name__}, but of {type(fallback).__name__}")
        return self.value if self.is_present() else fallback

    def or_else_get(
        self: Maybe[T],
        supplier: Callable[[], T],
        *,
        _coerce: bool = False
    ) -> T:
        supplied_value = supplier()
        if _coerce:
            from type_validation import _validate_or_coerce_value
            supplied_value = _validate_or_coerce_value(supplied_value, self.item_type, _coerce=_coerce)
        if not isinstance(supplied_value, self.item_type):
            raise TypeError(f"Supplied obj {supplied_value} is not of type {self.item_type.__name__}, but of {type(supplied_value).__name__}")
        return self.value if self.is_present() else supplied_value

    def or_else_raise(self: Maybe[T], exception_supplier: Callable[[], Exception]) -> T:
        if self.is_present():
            return self.value
        raise exception_supplier()

    def if_present(self: Maybe[T], consumer: Callable[[T], None]) -> None:
        if self.is_present():
            consumer(self.value)

    def map[U](self: Maybe[T], f: Callable[[T], U]) -> Maybe[U]:
        if self.value is None:
            raise ValueError("There's no obj to apply the function to.")
        result = f(self.value)
        if result is None:
            raise ValueError("Callable function returned a None obj.")
        return Maybe.of(result)

    def map_or_else[U](
        self: Maybe[T],
        f: Callable[[T], U],
        fallback: U,
        *,
        _coerce: bool = False
    ) -> U:
        if _coerce:
            from type_validation import _validate_or_coerce_value
            fallback = _validate_or_coerce_value(fallback, self.item_type, _coerce=_coerce)
        return f(self.value) if self.is_present() else fallback

    def flatmap[U](
        self: Maybe[T],
        f: Callable[[T], Maybe[U]]
    ) -> U:
        if self.is_empty():
            raise ValueError("There's no obj to apply the function to.")
        result = f(self.value)
        if not isinstance(result, Maybe):
            raise TypeError("flatmap mapper must return a Maybe object.")
        if result.is_empty():
            raise ValueError("flatmap mapper returned an empty obj.")
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
        return f"{type(self)}.of({self.value!r})" if self.is_present() else f"{type(self)}.empty()"
