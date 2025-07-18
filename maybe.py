from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Callable, TypeVar, TYPE_CHECKING, get_args, ClassVar, Any
from weakref import WeakKeyDictionary, WeakValueDictionary


@dataclass(frozen=True, slots=True, repr=False)
class Maybe[T]:

    item_type: type[T]
    value: T | None
    _generic_type_registry: ClassVar[WeakValueDictionary[tuple[type, type], type]] = WeakValueDictionary()

    def __init__(
        self: Maybe[T],
        value: T | None = None,
        *,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        from type_validation import _validate_or_coerce_value

        try:
            generic_item_type = self.__class__._inferred_item_type
        except (AttributeError, IndexError, TypeError, KeyError):
            generic_item_type = None

        actual_value = value if _skip_validation else _validate_or_coerce_value(generic_item_type, value, _coerce) if value is not None else None

        object.__setattr__(self, 'item_type', generic_item_type)
        object.__setattr__(self, 'value', actual_value)

    @classmethod
    def __class_getitem__(cls: type[Maybe[T]], item: Any):
        cache_key = (cls, item)
        if cache_key in cls._generic_type_registry:
            return cls._generic_type_registry[cache_key]

        name = f"__{cls.__name__}[{getattr(item, '__name__', repr(item))}]__"
        subclass = type(
            name,
            (cls,),
            {
                "__name__": cls.__name__,
                "_inferred_item_type": item,
            },
        )
        cls._generic_type_registry[cache_key] = subclass
        return subclass

    @classmethod
    def empty(cls, item_type: type[T]) -> Maybe[T]:
        return Maybe[item_type](None)

    @classmethod
    def of(cls, value: T) -> Maybe[T]:
        if value is None:
            raise ValueError("Can't use Maybe.of with a None value.")
        from type_validation import _infer_type
        return Maybe[_infer_type(value)](value)

    @classmethod
    def of_nullable(cls, value: T | None, item_type: type[T]) -> Maybe[T]:
        if item_type is None:
            raise ValueError("You must give a type when using Maybe.of_nullable")
        from type_validation import _validate_or_coerce_value
        return Maybe[item_type](_validate_or_coerce_value(value))

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

    def map[U](self: Maybe[T], f: Callable[[T], U]) -> Maybe[U]:
        if self.value is None:
            raise ValueError("There's no value to apply the function to.")
        result = f(self.value)
        if result is None:
            raise ValueError("Callable function returned a None value.")
        return Maybe.of(result)

    def map_or_else[U](
        self: Maybe[T],
        f: Callable[[T], U],
        fallback: U,
        coerce: bool = False
    ) -> U:
        if coerce:
            from type_validation import _validate_or_coerce_value
            fallback = _validate_or_coerce_value(self.item_type, fallback, coerce)
        return f(self.value) if self.is_present() else fallback

    def flatmap[U](
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
