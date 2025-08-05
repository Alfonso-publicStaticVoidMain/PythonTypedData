from __future__ import annotations

from typing import Callable, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from abstract_classes.abstract_dict import AbstractDict
    from abstract_classes.collection import Collection
from abstract_classes.generic_base import forbid_instantiation


@forbid_instantiation
class Metadata:

    @classmethod
    def _get_finisher(
        cls: type[Metadata],
        default: Callable[[Iterable], Iterable] = lambda x : x
    ) -> Callable[[Iterable], Iterable]:
        """
        Gets a callable that is applied to the values of this class's objects on init before setting the attribute.

        :param default: Default value if the class doesn't have a _finisher attribute.
        :type default: Callable[[Iterable], Iterable]

        :return: The _finisher attribute of the class, or a default if it doesn't have one.
        :rtype: Callable[[Iterable], Iterable]
        """
        return getattr(cls, '_finisher', default)

    @classmethod
    def _get_skip_validation_finisher(
        cls: type[Metadata],
        default: Callable[[Iterable], Iterable] = lambda x : x
    ) -> Callable[[Iterable], Iterable]:
        """
        Gets a callable that is applied to the values on init when skipping validation to avoid forwarding the reference.

        :param default: Default value if the class doesn't have a _skip_validation_finisher attribute.
        :type default: Callable[[Iterable], Iterable]

        :return: The _skip_validation_finisher attribute of the class, or a default if it doesn't have one.
        :rtype: Callable[[Iterable], Iterable]
        """
        return getattr(cls, '_skip_validation_finisher', default)

    @classmethod
    def _get_repr_finisher(
        cls: type[Metadata],
        default: Callable[[Iterable], Iterable] = lambda x : x
    ) -> Callable[[Iterable], Iterable]:
        """
        Gets a callable that is applied to the values of this class's objects when representing them as a string.

        :param default: Default value if the class doesn't have a _repr_finisher attribute.
        :type default: Callable[[Iterable], Iterable]

        :return: The _repr_finisher attribute of the class, or a default if it doesn't have one.
        :rtype: Callable[[Iterable], Iterable]
        """
        return getattr(cls, '_repr_finisher', default)

    @classmethod
    def _get_eq_finisher(
        cls: type[Metadata],
        default: Callable[[Iterable], Iterable] = lambda x : x
    ) -> Callable[[Iterable], Iterable]:
        """
        Gets a callable that is applied to the values of this class's objects when comparing with others.

        :param default: Default value if the class doesn't have a _eq_finisher attribute.
        :type default: Callable[[Iterable], Iterable]

        :return: The _eq_finisher attribute of the class, or a default if it doesn't have one.
        :rtype: Callable[[Iterable], Iterable]
        """
        return getattr(cls, '_eq_finisher', default)

    @classmethod
    def _get_comparable_types[T: Collection | AbstractDict](
        cls: type[T],
        default: type[T] | tuple[type[T], ...] | None = None  # The real default value is cls
    ) -> type[T] | tuple[type[T], ...]:
        """
        Gets the type or tuples of types this class can be expected to be possibly equal to.

        :param default: Default value if the class doesn't have a _comparable_types attribute. When None, the method
         returns cls instead in that case.
        :type default: type[T] | tuple[type[T], ...] | None

        :return: The _comparable_types attribute of the class, or a default if it doesn't have one.
        :rtype: type[T] | tuple[type[T], ...]
        """
        return getattr(cls, '_comparable_types', default) or cls

    @classmethod
    def _get_forbidden_iterable_types(
        cls: type[Metadata],
        default: type | tuple[type, ...] = ()
    ) -> type | tuple[type, ...]:
        """
        Gets the iterable types that can't be passed as values to this class's init.

        :param default: Default value if the class doesn't have a _forbidden_iterable_types attribute.
        :type default: type | tuple[type, ...]

        :return: The _forbidden_iterable_types attribute of the class, or a default if it doesn't have one.
        :rtype: type | tuple[type, ...]
        """
        return getattr(cls, '_forbidden_iterable_types', default)

    @classmethod
    def _get_allowed_ordered_types(
        cls: type[Metadata],
        default: type | tuple[type, ...] = ()
    ) -> type | tuple[type, ...]:
        """
        Gets the iterable types that can be assigned with the setitem method.

        :param default: Default value if the class doesn't have a _allowed_ordered_types attribute.
        :type default: type | tuple[type, ...]

        :return: The _allowed_ordered_types attribute of the class, or a default if it doesn't have one.
        :rtype: type | tuple[type, ...]
        """
        return getattr(cls, '_allowed_ordered_types', default)

    @classmethod
    def _get_priority(
            cls: type[Metadata],
            default: int = 100
    ) -> type | tuple[type, ...]:
        """
        Gets the priority of the class when deciding a return type.

        :param default: Default value if the class doesn't have a _priority attribute.
        :type default: type | tuple[type, ...]

        :return: The _priority attribute of the class, or a default if it doesn't have one.
        :rtype: type | tuple[type, ...]
        """
        return getattr(cls, '_priority', default)