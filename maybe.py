from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from GenericBase import GenericBase


@dataclass(frozen=True, slots=True, repr=False)
class Maybe[T](GenericBase[T]):
    """
    A container object which may or may not contain a non-None value.

    Inspired by Java's Optional, this class provides a way to explicitly handle the presence or absence of a value
    in a type-safe way. It is immutable, supports functional-style transformations, and some basic type validation and
    coercion systems.
    """

    item_type: type[T]
    value: T | None

    def __init__(
        self: Maybe[T],
        value: T | None = None,
        *,
        _coerce: bool = False,
        _skip_validation: bool = False
    ) -> None:
        """
        Basic constructor of the Maybe class, accepting a value or assuming it None if absent.

        Generic type is inferred from the generic with which Maybe was called, like Maybe[int].

        :param value: The wrapped value or None if empty.
        :type value: T | None

        :param _coerce: State parameter that, if True, attempts to coerce the value to the expected item_type.
        :type _coerce: bool

        :param _skip_validation: If True, disables runtime type validation of the value.
        :type _skip_validation: bool

        :raises ValueError: If the constructor was called without giving a generic type to Maybe. This forbids Maybe(1),
        for instance. Use Maybe.of(1) to infer the type.
        """
        from type_validation import _validate_or_coerce_value

        generic_item_type = type(self)._inferred_item_type()

        if generic_item_type is None:
            raise ValueError("Maybe constructor was called without generic a type parameter!")

        actual_value = value if _skip_validation else _validate_or_coerce_value(value, generic_item_type, _coerce=_coerce) if value is not None else None

        object.__setattr__(self, 'item_type', generic_item_type)
        object.__setattr__(self, 'value', actual_value)

    @classmethod
    def _inferred_item_type(cls: Maybe[T]) -> type[T] | None:
        """
        Returns the generic type argument T with which this Maybe subclass was parameterized, or None.

        This method is used internally for runtime type enforcement and generic introspection, and it fetches the generic
        type from the _args attribute the class inherits from GenericBase which is set on its __class_getitem__ method.

        :return: The generic type T that this class was called upon, as stored on its attribute _args by the
        __class_getitem__ method inherited from GenericBase. If unable to retrieve it, returns None.
        :rtype: type[T] | None
        """
        try:
            return cls._args[0]
        except (AttributeError, IndexError, TypeError, KeyError):
            return None

    @classmethod
    def empty(cls) -> Maybe[T]:
        """
        Returns a Maybe object holding a None value, fetching the item_type from the class itself.

        :return: A Maybe object holding a None object. Its generic type is inferred from the dynamic Maybe subclass this
        method was called on, like Maybe[int].
        """
        return cls()

    @classmethod
    def of(cls, value: T) -> Maybe[T]:
        """
        Creates and returns a Maybe object containing the given value, and inferring its item_type from it.

        :param value: Value for the Maybe object to contain. Mustn't be None.
        :type value: T

        :return: A Maybe object containing the value.
        :rtype: Maybe[T]
        """
        if value is None:
            raise ValueError("Can't use Maybe.of with a None obj.")
        from type_validation import _infer_type
        return Maybe[_infer_type(value)](value, _skip_validation=True)

    @classmethod
    def of_nullable(cls, value: T | None, item_type: type[T]) -> Maybe[T]:
        """
        Creates and returns a Maybe object of the given type containing the given value.

        :param value: Value for the Maybe object to contain. Can be None.
        :type value: T

        :param item_type: Type for the Maybe object to hold. It must always be provided.
        :type: type[T]

        :return: A Maybe object of the given type containing the value.
        :rtype: Maybe[T]
        """
        if item_type is None:
            raise ValueError("You must give a type when using Maybe.of_nullable")
        from type_validation import _validate_or_coerce_value
        return Maybe[item_type](_validate_or_coerce_value(value, item_type)) if value is not None else Maybe[item_type]()

    def is_present(self: Maybe[T]) -> bool:
        """
        Determines whether this Maybe object holds a non-None value.

        :return: True if self's value is not None, False otherwise.
        :rtype: bool
        """
        return self.value is not None

    def is_empty(self: Maybe[T]) -> bool:
        """
        Determines whether this Maybe object holds a None value.

        :return: True if self's value is None, False otherwise.
        :rtype: bool
        """
        return self.value is None

    def get(self: Maybe[T]) -> T:
        """
        Gets the value contained in this Maybe object if not None. Raises an Error otherwise.

        :return: The value contained in this Maybe object, if able.
        :rtype: T

        :raises ValueError: If the Maybe is empty, i.e., if its value is None.
        """
        if self.is_empty():
            raise ValueError("No obj present")
        return self.value

    def or_else(
        self: Maybe[T],
        fallback: T,
        *,
        _coerce: bool = False
    ) -> T:
        """
        Gets the value contained in this Maybe object, or a fallback if it was empty.

        :param fallback: Value to return if self is empty.
        :type fallback: T

        :param _coerce: State parameter that, if True, attempts to coerce the fallback value.
        :type _coerce: bool

        :return: The value contained in this Maybe, or fallback if empty.
        :rtype: T

        :raises TypeError: If the fallback given doesn't validate the Maybe item_type, or can't be coerced to it if
        that option is enabled. This happens even if the fallback isn't needed.
        """
        from type_validation import _validate_or_coerce_value
        fallback = _validate_or_coerce_value(fallback, self.item_type, _coerce=_coerce)
        return self.value if self.is_present() else fallback

    def or_else_get(
        self: Maybe[T],
        supplier: Callable[[], T],
        *,
        _coerce: bool = False
    ) -> T:
        """
        Gets the value contained in this Maybe object, or a fallback obtained from a supplier if it was empty.

        :param supplier: Supplier to get the fallback value from.
        :type supplier: Callable[[], T]

        :param _coerce: State parameter that, if True, attempts to coerce the fallback value.
        :type _coerce: bool

        :return: The value contained in this Maybe, or a call from the supplier if empty.
        :rtype: T

        :raises TypeError: If the fallback given by the supplier doesn't validate the Maybe item_type, or can't be
        coerced to it if that option is enabled. This happens even if the fallback isn't needed.
        """
        return self.or_else(supplier(), _coerce=_coerce)

    def or_else_raise(self: Maybe[T], exception_supplier: Callable[[], Exception]) -> T:
        """
        Gets the value contained in this Maybe object, or raises an exception if it was empty.

        :param exception_supplier: Supplier to get the exception if self was empty.
        :type exception_supplier: Callable[[], Exception]

        :return: The value contained in this Maybe, if able.
        :rtype: T

        :raises Exception: Of the type provided by the exception_supplier, if self was empty.
        """
        if self.is_present():
            return self.value
        raise exception_supplier()

    def if_present(self: Maybe[T], consumer: Callable[[T], None]) -> None:
        """
        Applies a consumer to the value contained in this Maybe object, if any is present.

        :param consumer: Consumer function to apply to the value.
        :type consumer: Callable[[T], None]
        """
        if self.is_present():
            consumer(self.value)

    def map[U](
        self: Maybe[T],
        f: Callable[[T], U],
        result_type: type[U] | None = None,
        _coerce: bool = False
    ) -> Maybe[U]:
        """
        Maps the non-None value of this Maybe to another Maybe, setting or inferring its new type.

        :param f: Mapper function to apply to the value.
        :type f: Callable[[T], U]

        :param result_type: Expected result type of the mapper.
        :type result_type: type[U] | None

        :param _coerce: State parameter that, if True, attempts to coerce the result value to the expected result_type.
        :type _coerce: bool

        :return: A Maybe object containing the mapped value. Its type is given explicitly on result_type or inferred.
        """
        if self.value is None:
            raise ValueError("There's no obj to apply the function to.")
        result = f(self.value)
        if result is None:
            raise ValueError("Callable function returned a None obj.")
        if result_type is not None:
            from type_validation import _validate_or_coerce_value
            return Maybe[result_type](result, _coerce=_coerce)
        return Maybe.of(result)

    def map_or_else[U](
        self: Maybe[T],
        f: Callable[[T], U],
        fallback: U
    ) -> U:
        """
        Maps the value of this Maybe and returns the result directly, or a fallback if self is empty.

        :param f: Mapper function to apply to the value.
        :type f: Callable[[T], U]

        :param fallback: Value to return if self is empty.
        :type fallback: U

        :return: The direct mapped value or the fallback if self was empty.
        :rtype: U
        """
        return f(self.value) if self.is_present() else fallback

    def flatmap[U](
        self: Maybe[T],
        f: Callable[[T], Maybe[U]],
        result_type: type[U] | None = None,
        _coerce: bool = False
    ) -> Maybe[U]:
        """
        Maps the value of this Maybe object by a Maybe-returning function and flattens the result before returning it.

        :param f: Mapper function to apply to the value.
        :type f: Callable[[T], Maybe[U]]

        :param result_type: Expected result type of the Maybe of the mapper.
        :type result_type: type[U] | None

        :param _coerce: State parameter that, if True, attempts to coerce the result value to the expected result_type.
        :type _coerce: bool

        :return: The
        """
        if self.is_empty() and result_type is not None:
            return Maybe[result_type].empty()
        result = f(self.value)
        if not isinstance(result, Maybe):
            raise TypeError("flatmap mapper must return a Maybe object.")
        if result.is_empty():
            raise ValueError("flatmap mapper returned an empty obj.")
        if result_type is not None:
            return Maybe[result_type](result.get(), _coerce=_coerce)
        return result

    def filter(
        self: Maybe[T],
        predicate: Callable[[T], bool]
    ) -> Maybe[T]:
        """
        Returns self if its value verifies the predicate, or an empty Maybe of the same type otherwise.

        :param predicate: Mapping to the booleans to filter for.
        :type predicate: Callable[[T], bool]

        :return: Self if its value verifies the predicate, or an empty Maybe of the same type otherwise.
        :rtype: Maybe[T]
        """
        return self if self.is_present() and predicate(self.value) else type(self).empty()

    def __bool__(self: Maybe[T]) -> bool:
        """
        Delegates the bool implementation to that of the value's.

        :return: True if the value is evaluated to True by bool(), False otherwise or if it's None.
        :rtype: bool
        """
        return bool(self.value)

    def __repr__(self: Maybe[T]) -> str:
        """
        Gives a str representation of this Maybe object, displaying its wrapped value or indicating if it holds None.

        :return: A str of the format Maybe[self.item_type].of(self.value), or Maybe[self.item_type].empty().
        :rtype: str
        """
        from abstract_classes import class_name
        return f"{class_name(type(self))}.of({self.value!r})" if self.is_present() else f"{class_name(type(self))}.empty()"
