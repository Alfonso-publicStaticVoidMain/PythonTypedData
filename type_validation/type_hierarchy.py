from typing import get_origin, get_args, Union, Any
from types import UnionType

from abstract_classes.generic_base import GenericBase


def _get_origin_args(tp: type) -> tuple[type, tuple[type, ...]]:
    """
    Gets the origin and args of a type or TypeAlias, modified to work with Collections and AbstractDicts too.

    :param tp: Type to get the origin and args of.
    :type tp: type

    :return: A tuple of a type and a tuple of types representing the origin class and the args it was called upon.
    :rtype: tuple[type, tuple[type, ...]]
    """
    origin = type(None) if tp is None else get_origin(tp)
    args = get_args(tp)

    if origin is None and hasattr(tp, "_origin"):
        origin = tp._origin
        args = getattr(tp, "_args", ())

    return origin or tp, args


def _is_subtype(tp: type, other: type) -> bool:
    """
    Checks if the first type is a subtype of the other or not, accounting for unions and generics.

    :param tp: Type to check if it's a subtype.
    :type tp: type

    :param other: Type to check if it's a supertype.
    :type other: type

    :return: True if tp is a subtype of other, accounting for union of types and generics. False otherwise.
    :rtype: bool
    """
    tp_origin, tp_args = _get_origin_args(tp)
    other_origin, other_args = _get_origin_args(other)

    # Any is supertype to everything and subtype only to itself
    if other is Any:
        return True
    if tp is Any:
        return other is Any

    # If "tp" is a Union
    if tp_origin in (Union, UnionType):
        if other_origin in (Union, UnionType):
            # Coverage rule: each arg in tp matches at least one arg in other
            return all(
                any(_is_subtype(t_arg, o_arg) for o_arg in other_args)
                for t_arg in tp_args
            )
        else:
            # Non-union other: all members of tp must be subtypes of other
            return all(
                _is_subtype(t_arg, other)
                for t_arg in tp_args
            )

    # If "other" is a Union
    if other_origin in (Union, UnionType):
        return any(
            _is_subtype(tp, o_arg)
            for o_arg in other_args
        )

    # Regular origin check
    if not issubclass(tp_origin, other_origin):
        return False

    # Generic argument compatibility (tuple special case included)
    if other_args:
        if not tp_args:
            return False

        # Special tuple[...] handling
        if tp_origin is tuple and other_origin is tuple:
            if len(other_args) == 2 and other_args[1] is Ellipsis:
                if len(tp_args) == 2 and tp_args[1] is Ellipsis:
                    return _is_subtype(tp_args[0], other_args[0])
                else:
                    return all(_is_subtype(arg, other_args[0]) for arg in tp_args)
            if len(tp_args) != len(other_args):
                return False
            return all(_is_subtype(t_arg, o_arg) for t_arg, o_arg in zip(tp_args, other_args))

        # Normal generics
        if len(tp_args) != len(other_args):
            return False
        for t_arg, o_arg in zip(tp_args, other_args):
            if not _is_subtype(t_arg, o_arg):
                return False

    return True


def _get_supertype(t: type, other: type) -> type:
    """
    Gets the type from among two types that is supertype to the other. If unable, raises an error.

    Commutativity is expected of this function.

    :param t: First type to check.
    :type t: type

    :param other: Second type to check.
    :type other: type

    :return: The type from among the two that the is supertype to the other.
    :type: type

    :raises TypeError: If none of the give types is supertype to the other.
    """
    if _is_subtype(t, other):
        return other
    if _is_subtype(other, t):
        return t
    raise TypeError(f"No supertype between {t.__name__} and {other.__name__}")


def _get_subtype(t: type, other: type) -> type:
    """
    Gets the type from among two types that is subtype to the other. If unable, raises an error.

    Commutativity is expected of this function.

    :param t: First type to check.
    :type t: type

    :param other: Second type to check.
    :type other: type

    :return: The type from among the two that the is subtype to the other.
    :type: type

    :raises TypeError: If none of the give types is subtype to the other.
    """
    if _is_subtype(t, other):
        return t
    if _is_subtype(other, t):
        return other
    raise TypeError(f"No subtype between {t.__name__} and {other.__name__}")


def _resolve_type_priority[G: GenericBase](t: type[G], other: type[G]) -> type[G]:
    origin_t = getattr(t, "_origin", t)
    origin_other = getattr(other, "_origin", other)

    # If origins are the same, return either type
    if origin_t is origin_other:
        return t

    # Origins must be comparable
    if not (_is_subtype(origin_t, origin_other) or _is_subtype(origin_other, origin_t)):
        raise TypeError(f"Incompatible origins: {origin_t} and {origin_other}")

    # Mutability check
    mutable_t = getattr(t, "_mutable", False)
    mutable_other = getattr(other, "_mutable", False)
    if mutable_t != mutable_other:
        return other if mutable_t else t  # prefer the one without _mutable

    # Priority logic
    has_priority_t = hasattr(t, "_priority")
    has_priority_other = hasattr(other, "_priority")

    if has_priority_t and has_priority_other:
        priority_t = t._priority
        priority_other = other._priority
        if priority_t == priority_other:
            raise TypeError(f"Both {origin_t.__name__} and {origin_other.__name__} have the same priority {priority_t}!")
        return t if priority_t < priority_other else other

    if has_priority_t:
        return t
    if has_priority_other:
        return other

    # Neither has _priority
    raise TypeError(f"Cannot resolve type priority between {origin_t.__name__} and {origin_other.__name__}: no _priority set for either.")

