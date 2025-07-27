from __future__ import annotations

from typing import Any, Callable, Iterable, TypeVar, Iterator

from abstract_classes.collection import Collection
from abstract_classes.generic_base import GenericBase, forbid_instantiation
from abstract_classes.abstract_set import AbstractSet


@forbid_instantiation
class AbstractTuple[*Ts](GenericBase[*Ts]):

    values: Any
    item_types: tuple[type, ...]

    def __init__(
        self: AbstractTuple[*Ts],
        *values: type[*Ts],
        _coerce: bool = False,
        _forbidden_iterable_types: tuple[type, ...] = (AbstractSet, set, frozenset),
        _finisher: Callable[[Iterable], Any] = None,
        _skip_validation: bool = False
    ) -> None:
        from type_validation.type_validation import _validate_tuple, _validate_or_coerce_tuple

        item_types: tuple[type, ...] = type(self)._inferred_item_type()

        if item_types is None:
            raise TypeError(f"{type(self).__name__} must be instantiated with a generic type, e.g., MutableList[int](...) or via .of().")

        if any(isinstance(tp, TypeVar) is None for tp in item_types):
            raise TypeError(f"{type(self).__name__} was instantiated without a generic type, somehow {item_types} was a TypeVar.")

        if (
            len(values) == 1  # The values are of length 1.
            and not _validate_tuple(tuple(values[0]), item_types)  # Their only value doesn't validate the expected type.
            and isinstance(values[0], Iterable)  # Their only value is an Iterable.
            and not isinstance(values[0], (str, bytes))  # But it's not a str or bytes.
        ):
            values = values[0]  # Then, the values are unpacked.

        if isinstance(values, _forbidden_iterable_types):
            raise TypeError(f"Invalid type {type(values).__name__} for class {type(self).__name__}.")

        object.__setattr__(self, 'item_types', item_types)

        final_values = values if _skip_validation else _validate_or_coerce_tuple(values, self.item_types, _coerce=_coerce)

        _finisher = _finisher or getattr(type(self), '_finisher', lambda x : x)

        object.__setattr__(self, 'values', _finisher(final_values))

    @classmethod
    def _inferred_item_type(cls: type[AbstractTuple[*Ts]]) -> tuple[type, ...] | None:
        try:
            return cls._args
        except (AttributeError, IndexError, TypeError, KeyError):
            return None

    @classmethod
    def of(cls: type[AbstractTuple], *values: Any) -> AbstractTuple[*Ts]:
        if len(values) == 1 and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            values = tuple(values[0])
        from type_validation.type_validation import _infer_type_contained_in_tuple
        return cls[_infer_type_contained_in_tuple(values)](values, _skip_validation=True)

    def __len__(self: AbstractTuple[*Ts]) -> int:
        """
        Returns the number of elements in the tuple by delegating to the internal container's __len__ method.

        :return: The length of the internal container.
        :rtype: int
        """
        return len(self.values)

    def __iter__(self: AbstractTuple[*Ts]) -> Iterator:
        """
        Returns an iterator over the values in the tuple's internal container.

        :return: An iterable over the values of the tuple.
        :rtype: Iterator[T]
        """
        return iter(self.values)