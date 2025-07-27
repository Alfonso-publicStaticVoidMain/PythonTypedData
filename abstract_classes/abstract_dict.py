from __future__ import annotations

from typing import ClassVar, Callable, Any, Mapping, Iterable, TypeVar, Iterator

from immutabledict import immutabledict

from abstract_classes.GenericBase import GenericBase, class_name
from abstract_classes.generic_base import forbid_instantiation


@forbid_instantiation
class AbstractDict[K, V](GenericBase[K, V]):
    """
    Abstract base class representing a dictionary with type enforced keys and values given by generic types.

    Provides a base class for storing and operating on dictionaries with keys and values of a common type each. It uses
    generics to enforce runtime type safety and supports fluent and functional-style operations inspired by Java's
    Stream API.

    The class enforces runtime generic type tracking using a metaclass extension (GenericBase), allowing validation
    and coercion of elements during construction and transformations. It cannot be directly instantiated and must be
    parameterized by two concrete types when the constructor is called (e.g., MutableDict[int, str]).

    Attributes:
        key_type (type[K]): The type constraint for keys.
        value_type (type[V]): The type constraint for values.
        data (dict[K, V]): The underlying dictionary storage.

    Note:
        Any method that returns a new AbstractDict instance (e.g., filter, map, etc.) constructs the returned
        value using type(self)(...). This ensures that:

            - The returned object has the same concrete runtime subclass as self.
            - Generic type parameters (K, V) are preserved without reapplying __class_getitem__, because they are
              already bound via the dynamic subclassing mechanism in __class_getitem__.

        This makes behavior consistent across all subclasses of AbstractDict: type(self) guarantees the returned value
        matches the exact type and structure of self, unless otherwise explicitly overridden. Also, calling
        type(self)[new_key_type, new_value_type] correctly creates a new dynamic subclass with the same base class as
        self but with the new generic types.
    """

    key_type: type[K]
    value_type: type[V]
    data: dict[K, V]

    _finisher: ClassVar[Callable[[dict], Any]] = immutabledict

    def __init__(
        self: AbstractDict[K, V],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None = None,
        *,
        _keys: Iterable[K] | None = None,
        _values: Iterable[V] | None = None,
        _coerce_keys: bool = False,
        _coerce_values: bool = False,
        _finisher: Callable[[dict[K, V]], Any] = None,
        _skip_validation: bool = False
    ) -> None:
        """
        Initialize an AbstractDict with type validation and optional coercion.

        :param keys_values: A dict, mapping, iterable of (key, value) tuples, or another AbstractDict.
        :type keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V] | None

        :param _keys: Optional keys iterable used in conjunction with `_values`.
        :type _keys: Iterable[K] | None

        :param _values: Optional values iterable used in conjunction with `_keys`.
        :type _values: Iterable[V] | None

        :param _coerce_keys: Whether to coerce keys to the declared type.
        :type _coerce_keys: bool

        :param _coerce_values: Whether to coerce values to the declared type.
        :type _coerce_values: bool

        :param _finisher: Callable applied to the final dict (defaults to identity).
        :type _finisher: Callable[[dict[K, V]], Any]

        :param _skip_validation: If True, skips all type validation and coercion.
        :type _skip_validation: bool
        """
        from type_validation.type_validation import (
            _validate_or_coerce_iterable,
            _split_keys_values,
            _validate_duplicates_and_hash
        )

        key_type, value_type = type(self)._inferred_key_value_types()

        if key_type is None or value_type is None:
            raise TypeError(f"Not all generic types were provided. Key: {key_type} | Value: {value_type}")

        if isinstance(key_type, TypeVar) or isinstance(value_type, TypeVar):
            raise TypeError(f"Generic types must be fully specified for {type(self).__name__}. Use {type(self)._origin.__name__}.of(...) to infer types from iterable.")

        object.__setattr__(self, "key_type", key_type)
        object.__setattr__(self, "value_type", value_type)

        _finisher = _finisher or getattr(type(self), '_finisher', lambda x: x)

        if keys_values is None and (_keys is None or _values is None):
            object.__setattr__(self, "data", _finisher({}))
            return

        if _keys is not None and _values is not None:
            keys = _keys
            values = _values
            if len(list(keys)) != len(list(values)):
                raise ValueError("Keys and iterable must be of the same length.")
            keys_from_iterable = True
        else:
            keys, values, keys_from_iterable = _split_keys_values(keys_values)

        actual_keys = keys if _skip_validation else _validate_or_coerce_iterable(keys, self.key_type, _coerce=_coerce_keys)
        actual_values = values if _skip_validation else _validate_or_coerce_iterable(values, self.value_type, _coerce=_coerce_values)

        if keys_from_iterable:
            _validate_duplicates_and_hash(actual_keys)

        object.__setattr__(self, "data", _finisher(dict(zip(actual_keys, actual_values))))

    @classmethod
    def _inferred_key_value_types(cls: AbstractDict[K, V]) -> tuple[type[K] | None, type[V] | None]:
        """
        Returns the inferred key and value types for this class if they were provided.

        This method inspects the generic arguments applied to the class, stored in its _args attribute inherited from
        GenericBase and returns them. It returns (None, None) if the types are not yet specified.

        :return: Tuple of (key_type, value_type) or (None, None) if not inferred.
        :rtype: tuple[type[K] | None, type[V] | None]
        """
        try:
            key_type = cls._args[0]
            value_type = cls._args[1]
        except (TypeError, ValueError, IndexError, KeyError):
            key_type = None
            value_type = None
        return key_type, value_type

    @classmethod
    def of(
        cls: type[AbstractDict[K, V]],
        keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]
    ) -> AbstractDict[K, V]:
        """
        Infer key/value types from the input and construct an AbstractDict containing them.

        :param keys_values: The data to infer types from and use to initialize the dictionary.
        :type keys_values: dict[K, V] | Mapping[K, V] | Iterable[tuple[K, V]] | AbstractDict[K, V]

        :return: A new AbstractDict with inferred generic types and properly validated contents (hashable and not
        duplicated keys).
        :rtype: AbstractDict[K, V]
        """
        if keys_values is None or not keys_values:
            raise ValueError(f"Can't create a {cls.__name__} object from empty iterable.")
        from type_validation.type_validation import _infer_type_contained_in_iterable, _split_keys_values
        keys, values, _ = _split_keys_values(keys_values)
        key_type = _infer_type_contained_in_iterable(keys)
        value_type = _infer_type_contained_in_iterable(values)
        return cls[key_type, value_type](_keys=keys, _values=values)

    @classmethod
    def of_keys_values(
        cls: type[AbstractDict[K, V]],
        keys: Iterable[K],
        values: Iterable[V]
    ) -> AbstractDict[K, V]:
        """
        Constructs an AbstractDict from separate keys and values iterables, inferring their types.

        :param keys: An iterable of keys.
        :type keys: Iterable[K]

        :param values: An iterable of values, matching the length of `keys`.
        :type values: Iterable[V]

        :return: A new AbstractDict initialized from the given key-value pairs.
        :rtype: AbstractDict[K, V]

        :raises ValueError: If `keys` and `values` do not have the same length.
        """
        keys = list(keys)
        values = list(values)

        if len(keys) != len(values):
            raise ValueError("Keys and iterable must be of the same length when using .of_keys_values")

        from type_validation.type_validation import _infer_type_contained_in_iterable
        key_type = _infer_type_contained_in_iterable(keys)
        value_type = _infer_type_contained_in_iterable(values)
        return cls[key_type, value_type](_keys=keys, _values=values)

    def __getitem__(self: AbstractDict[K, V], key: K | slice) -> V | AbstractDict[K, V]:
        """
        Returns a value for a given key, or a sliced subdictionary for a slice of keys.

        - If a single key is passed, returns its associated value.
        - If a `slice` is passed (e.g., `dict[start:stop]`), returns a new `AbstractDict[K, V]`
          with all keys within that range. Step is not supported.

        :param key: A key of type K or a slice over the key space.
        :type key: K | slice

        :return: The value associated with the key, or a sliced subdictionary.
        :rtype: V | AbstractDict[K, V]

        :raises TypeError: If the keys are not orderable for slicing or if the slice step is not None.
        :raises KeyError: If the key is not found.
        """
        if isinstance(key, slice):
            # Subdict slicing
            if key.step is not None:
                raise TypeError("Step is not supported in dict slicing.")

            start, stop = key.start, key.stop

            sample_key: K | None = next(iter(self.data), None)
            if sample_key is None:
                return type(self)({})

            try:
                # Try comparing sample_key with start/stop if provided
                if start is not None:
                    sample_key >= start
                if stop is not None:
                    sample_key <= stop
            except TypeError:
                raise TypeError("Keys must support ordering for subdict slicing.")

            return self.filter_keys(
                lambda k: (start is None or start <= k) and (stop is None or k <= stop)
            )
        else:
            # Regular key access
            return self.data[key]

    def __iter__(self: AbstractDict[K, V]) -> Iterator[K]:
        """
        Returns an iterator over the keys of this AbstractDict.

        :return: An iterator over all keys.
        :rtype: Iterator[K]
        """
        return iter(self.data)

    def keys(self: AbstractDict[K, V]):
        """
        Returns a view of the dictionary's keys.
        :rtype: dict_keys[K]
        """
        return self.data.keys()

    def values(self: AbstractDict[K, V]):
        """
        Returns a view of the dictionary's values.
        :rtype: dict_values[V]
        """
        return self.data.values()

    def items(self: AbstractDict[K, V]):
        """
        Returns a view of the dictionary's key-value pairs.
        :rtype: dict_items[K, V]
        """
        return self.data.items()

    def __len__(self: AbstractDict[K, V]) -> int:
        """
        Returns the number of items in this AbstractDict.

        :return: The number of key-value pairs present.
        :rtype: int
        """
        return len(self.data)

    def __contains__(self: AbstractDict[K, V], key: Any) -> bool:
        """
        Checks whether the given key is present on the AbstractDict.

        :param key: The key to check.
        :type key: Any

        :return: True if the key exists, False otherwise.
        :rtype: bool
        """
        return key in self.data

    def __eq__(self: AbstractDict[K, V], other: Any) -> bool:
        """
        Checks equality with another AbstractDict.

        Two dictionaries are considered equal if they share the same class, key/value types, and contents.

        :param other: The object to compare against.
        :type other: Any

        :return: True if `other` is an AbstractDict with the same key and values types and contents, False otherwise.
        :rtype: bool
        """
        return (
            isinstance(other, AbstractDict)
            and self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.data == other.data
        )

    def __repr__(self: AbstractDict[K, V]) -> str:
        """
        Returns a concise string representation of this AbstractDict, including its generic types for keys and values.

        :return: A string representation of this AbstractDict.
        :rtype: str
        """

        return f"{class_name(type(self))}{dict(self.data)}"

    def __or__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns the union of this AbstractDict and another mapping.

        :param other: The other mapping to merge.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self containing all key-value pairs from both, with
        `other` overriding duplicate keys.
        :rtype: AbstractDict[K, V]
        """
        return type(self)(dict(self.data) | dict(other))

    def __and__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns the intersection of this AbstractDict with another mapping.

        :param other: The other mapping.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self with only keys present in both mappings.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({k: self.data[k] for k in self.data.keys() & other.keys()})

    def __sub__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns a new dictionary with the keys that are not in `other`.

        :param other: The mapping to subtract from this one.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self without the keys found in `other`.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({k: v for k, v in self.data.items() if k not in other})

    def __xor__(self: AbstractDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractDict[K, V]:
        """
        Returns the symmetric difference between this AbstractDict and another mapping.

        :param other: The other mapping.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: A new AbstractDict of the same dynamic subclass as self containing keys only in one of the two mappings.
        :rtype: AbstractDict[K, V]
        """
        sym_keys = self.data.keys() ^ other.keys()
        return type(self)({k: (self.data.get(k) or other.get(k)) for k in sym_keys})

    def to_dict(self: AbstractDict[K, V]) -> dict[K, V]:
        """
        Returns a shallow copy of the underlying data dictionary as a Python dict.

        :return: A native Python dictionary with the same contents.
        :rtype: dict[K, V]
        """
        return dict(self.data)

    def to_immutable_dict(self: AbstractDict[K, V]) -> immutabledict[K, V]:
        """
        Returns an immutabledict representation of the AbstractDict.

        :return: A frozen version of the current dictionary.
        :rtype: immutabledict[K, V]
        """
        return immutabledict(self.data)

    def copy(self: AbstractDict[K, V], deep: bool = False) -> AbstractDict[K, V]:
        """
        Returns a shallow or deep copy of the AbstractDict.

        If the underlying data dictionary implements `.copy()`, it uses that method for shallow copies. For deep copies,
        it uses `deepcopy` to recursively duplicate all contents. Skips re-validation for performance.

        The result is of the same dynamic subclass as `self`, with identical key and value types.

        :param deep: Boolean state parameter to control if the copy is shallow or deep.
        :type deep: bool

        :return: A shallow or deep copy of the object.
        :rtype: AbstractDict[K, V]
        """
        from copy import deepcopy
        data = deepcopy(self.data) if deep else (self.data.copy() if hasattr(self.data, 'copy') else self.data)
        return type(self)(data, _skip_validation=True)

    def get(
        self: AbstractDict[K, V],
        key: K,
        fallback: V | None = None,
        *,
        _coerce_keys: bool = False,
        _coerce_values: bool = False
    ) -> V | None:
        """
        Returns the value for a given key if present, else returns a fallback (after optional coercion).

        :param key: The key to search for.
        :type key: K

        :param fallback: The fallback value if the key is missing.
        :type fallback: V | None

        :param _coerce_keys: Whether to coerce the input key to the key type.
        :type _coerce_keys: bool

        :param _coerce_values: Whether to coerce the fallback value if returned.
        :type _coerce_values: bool

        :return: The value assigned to the key in the dictionary, or the fallback.
        :rtype: V | None
        """
        from type_validation.type_validation import _validate_or_coerce_value
        try:
            return self.data[key]
        except KeyError:
            return (
                _validate_or_coerce_value(fallback, self.value_type, _coerce=_coerce_values)
                if fallback is not None
                else None
            )

    def map_values[R](
        self: AbstractDict[K, V],
        f: Callable[[V], R],
        result_type: type[R] | None = None,
        *,
        _coerce_values: bool = False
    ) -> AbstractDict[K, R]:
        """
        Applies a function to all values and returns a new AbstractDict with the updated values.

        The key type is preserved, and the resulting value type can either be inferred or provided manually.
        The output dictionary is of the same subclass as self.

        :param f: A function mapping each value to a new value.
        :type f: Callable[[V], R]

        :param result_type: Optional explicit result type for values after transformation.
        :type result_type: type[R] | None

        :param _coerce_values: State parameter that, if True, coerces the transformed values to the given result type.
        :type _coerce_values: bool

        :return: A new AbstractDict of the same subclass as self with transformed values. Its key type is the same as
        self, and its value type is either inferred from the mapped values or taken from result_type if it's not None.
        :rtype: AbstractDict[K, R]
        """
        new_data = {key : f(value) for key, value in self.data.items()}
        if result_type is not None:
            return type(self)[self.key_type, result_type](new_data, _coerce_values=_coerce_values)
        else:
            from type_validation.type_validation import _infer_type_contained_in_iterable
            inferred_return_type = _infer_type_contained_in_iterable(new_data.values())
            return type(self)[self.key_type, inferred_return_type](new_data, _skip_validation=True)

    def filter_keys(self: AbstractDict[K, V], predicate: Callable[[K], bool]) -> AbstractDict[K, V]:
        """
        Returns a new AbstractDict containing only the (key, value) pairs whose keys satisfy a predicate.

        :param predicate: A function to the booleans that returns True for keys to retain.
        :type predicate: Callable[[K], bool]

        :return: A new AbstractDict of the same dynamic subclass as self containing the filtered (key, value) pairs.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({key : value for key, value in self.data.items() if predicate(key)})

    def filter_values(self: AbstractDict[K, V], predicate: Callable[[V], bool]) -> AbstractDict[K, V]:
        """
        Returns a new AbstractDict containing only the (key, value) pairs whose values satisfy a predicate.

        :param predicate: A function to the booleans that returns True for values to retain.
        :type predicate: Callable[[V], bool]

        :return: A new AbstractDict of the same dynamic subclass as self containing the filtered (key, value) pairs.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({key : value for key, value in self.data.items() if predicate(value)})

    def filter_items(self: AbstractDict[K, V], predicate: Callable[[K, V], bool]) -> AbstractDict[K, V]:
        """
        Returns a new AbstractDict containing only the (key, value) pairs that satisfy a (key, value) predicate.

        :param predicate: A function that returns True for pairs to retain.
        :type predicate: Callable[[K, V], bool]

        :return: A new AbstractDict of the same dynamic subclass as self containing the filtered key-value pairs.
        :rtype: AbstractDict[K, V]
        """
        return type(self)({key : value for key, value in self.data.items() if predicate(key, value)})


@forbid_instantiation
class AbstractMutableDict[K, V](AbstractDict[K, V]):
    """
    Abstract base class for mutable dictionaries with type enforced keys and values.

    Inherits from AbstractDict, extending it with mutation operations such as item assignment, deletion, and updates.
    It is still an abstract class, so it must be subclassed to create concrete implementations.

    It overrides _finisher to dict to ensure the mutability of the internal container, and also adds the attribute
    _mutable set to True as class metadata, that for now is unused.
    """

    _finisher: ClassVar[Callable[[dict], Mapping]] = dict
    _mutable: bool = True

    def __setitem__(self: AbstractMutableDict[K, V], key: K, value: V) -> None:
        """
        Inserts or updates a key-value pair in this AbstractMutableDict.

        Both the key and value are validated against their expected types.

        :param key: The key to insert or update.
        :type key: K

        :param value: The value to associate with the key.
        :type value: V
        """
        from type_validation.type_validation import _validate_or_coerce_value
        self.data[_validate_or_coerce_value(key, self.key_type)] = _validate_or_coerce_value(value, self.value_type)

    def __delitem__(self: AbstractMutableDict[K, V], key: K) -> None:
        """
        Deletes a key-value pair from this AbstractMutableDict by key.

        :param key: The key to remove.
        :type key: K
        :raises KeyError: If the key does not exist.
        """
        del self.data[key]

    def clear(self: AbstractMutableDict[K, V]) -> None:
        """
        Removes all key-value pairs from this AbstractMutableDict.
        """
        self.data.clear()

    def __ior__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place union update with another mapping.

        Equivalent to calling `.update()` with the given mapping. Values from `other` override any existing values.

        :param other: A mapping containing the new key-value pairs to update.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        self.update(other)
        return self

    def __iand__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place intersection with another mapping by removing keys not present in `other`.

        :param other: The mapping to intersect keys with.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        keys_to_remove = set(self.data) - set(other)
        for key in keys_to_remove:
            del self.data[key]
        return self

    def __isub__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place difference by removing keys found in `other`.

        :param other: The mapping whose keys will be removed.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        for key in other:
            self.data.pop(key, None)
        return self

    def __ixor__(self: AbstractMutableDict[K, V], other: AbstractDict[K, V] | Mapping[K, V]) -> AbstractMutableDict[K, V]:
        """
        In-place symmetric difference update with another mapping, keeping only the keys found in one but not both.

        :param other: The mapping to symmetrically differentiate with.
        :type other: AbstractDict[K, V] | Mapping[K, V]

        :return: The updated AbstractMutableDict.
        :rtype: AbstractMutableDict[K, V]
        """
        for key in other:
            if key in self.data:
                del self.data[key]
            else:
                self.data[key] = other[key]
        return self

    def update(
        self: AbstractMutableDict[K, V],
        other: dict[K, V] | Mapping[K, V] | AbstractDict[K, V],
        *,
        _coerce_keys: bool = True,
        _coerce_values: bool = True
    ) -> None:
        """
        Updates this AbstractMutableDict with the contents of another mapping.

        Values from `other` override existing values for their keys.

        :param other: The mapping to merge into this AbstractMutableDict.
        :type other: dict[K, V] | Mapping[K, V] | AbstractDict[K, V]

        :param _coerce_keys: State parameter that, if True, attempts to coerce keys before validation.
        :type _coerce_keys: bool

        :param _coerce_values: State parameter that, if True, attempts to coerce values before validation.
        :type _coerce_values: bool
        """
        from type_validation.type_validation import _validate_or_coerce_iterable

        validated_keys = _validate_or_coerce_iterable(other.keys(), self.key_type, _coerce=_coerce_keys)
        validated_values = _validate_or_coerce_iterable(other.values(), self.value_type, _coerce=_coerce_values)
        other_items = dict(zip(validated_keys, validated_values)).items()

        for key, value in other_items:
            self[key] = value

    def pop(
        self: AbstractMutableDict[K, V],
        key: K,
        fallback: V | None = None,
        *,
        _coerce_keys: bool = None,
        _coerce_values: bool = None
    ) -> V:
        """
        Removes and returns the value associated with a key, or a fallback if not found.

        :param key: The key to remove.
        :type key: K

        :param fallback: Optional fallback value if key is not present.
        :type fallback: V | None

        :param _coerce_keys: State parameter that, if True, attempts to coerce the key before popping.
        :type _coerce_keys: bool | None

        :param _coerce_values: State parameter that, if True, attempts to coerce the fallback before returning it.
        :type _coerce_values: bool | None

        :return: The value associated with the removed key or the fallback.
        :rtype: V
        """
        from type_validation.type_validation import _validate_or_coerce_value
        if fallback is not None:
            return self.data.pop(
                _validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys),
                _validate_or_coerce_value(fallback, self.value_type, _coerce=_coerce_values)
            )
        return self.data.pop(_validate_or_coerce_value(key, self.key_type, _coerce=_coerce_keys))

    def popitem(self: AbstractMutableDict[K, V]) -> tuple[K, V]:
        """
        Removes and returns the last inserted key-value pair.

        :return: A tuple of the removed key and value.
        :rtype: tuple[K, V]
        """
        return self.data.popitem()

    def setdefault(self: AbstractMutableDict[K, V], key: K, default: V | None = None) -> V:
        """
        Returns the value for a key, inserting a default value if the key is not present.

        :param key: The key to look up or insert.
        :type key: K

        :param default: The value to insert if the key is not present.
        :type default: V

        :return: The existing or newly inserted value.
        :rtype: V
        """
        from type_validation.type_validation import _validate_or_coerce_value
        if default is None:
            return self.data.setdefault(_validate_or_coerce_value(key, self.key_type))
        return self.data.setdefault(
            _validate_or_coerce_value(key, self.key_type),
            _validate_or_coerce_value(default, self.value_type)
        )
