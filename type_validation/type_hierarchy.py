from typing import get_origin, get_args, Union, Any
from types import UnionType

def _get_origin_args(tp: type) -> tuple[type, tuple[type, ...]]:
    """Return (origin, args) for typing generics and custom Collection generics."""
    origin = get_origin(tp)
    args = get_args(tp)

    if origin is None and hasattr(tp, "_origin"):
        origin = tp._origin
        args = getattr(tp, "_args", ())

    return origin or tp, args


def _is_subtype(tp: type, other: type) -> bool:
    """
    Returns True if tp is a subtype of other, considering origins, generics, and unions.
    Works with both typing generics and custom generic classes (nested supported).
    """
    tp_origin, tp_args = _get_origin_args(tp)
    other_origin, other_args = _get_origin_args(other)

    # Any is top type
    if other is Any:
        return True
    if tp is Any:
        return other is Any

    # If "tp" is a Union
    if tp_origin in (Union, UnionType):
        if other_origin in (Union, UnionType):
            # Coverage rule: each arg in tp matches at least one arg in other
            return all(
                any(
                    _is_subtype(
                        t_arg if t_arg is not None else type(None),
                        o_arg if o_arg is not None else type(None)
                    )
                    for o_arg in other_args
                )
                for t_arg in tp_args
            )
        else:
            # Non-union other: all members of tp must be subtypes of other
            return all(
                _is_subtype(t_arg if t_arg is not None else type(None), other)
                for t_arg in tp_args
            )

    # If "other" is a Union
    if other_origin in (Union, UnionType):
        return any(
            _is_subtype(tp, o_arg if o_arg is not None else type(None))
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
    """Return the 'bigger' type between t and other, or raise TypeError if unrelated."""
    if _is_subtype(t, other):
        return other
    if _is_subtype(other, t):
        return t
    raise TypeError(f"No supertype between {t.__name__} and {other.__name__}")



