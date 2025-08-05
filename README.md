A recreation of Java's Collection and Map interfaces within Python.

The base class for the inheritance tree is GenericBase\[*Ts\], a generic class accepting a TypedVarTuple, which adds the behaviour of storing the generic types given to the class with its implementation of \_\_class\_getitem\_\_ as a class attribute \_args.

The inheritance tree for the classes looks like this:

```
GenericBase[*Ts]
│
├── Collection[T]
│    │
│    ├── MutableCollection[T] 
│    │    │
│    │    │
│    ├────│── AbstractSequence[T]
│    │    │    ├── ImmutableList[T] (*)
│    │    ├────┴── AbstractMutableSequence[T]
│    │    │         └── MutableList[T] (*)
│    │    │
│    └────│── AbstractSet[T]
│         │    ├── ImmutableSet[T] (*)
│         └────┴── AbstractMutableSet[T]
│                   └── MutableSet[T] (*)
│
├── AbstractDict[K, V]
│    ├── ImmutableDict[K, V] (*)
│    └── AbstractMutableDict[K, V]
│         └── MutableDict[K, V] (*)
│
└── Maybe[T] (*)
```

Where classes marked with (\*) are concrete, and everything else abstract, hence their direct instantiation forbidden.

When calling a class `cls` extending from GenericBase with type parameters, like `MutableList\[int\]`, a new dynamic subclass of `cls` is generated, with an `_origin` attribute pointing to its original class, in this case `MutableList`, and an `_args` attribute storing in a tuple the generic types it was called upon, in this case, `(int,)`. If the type parameters included any TypeVar, no dynamic subclass is generated and the original `cls` is returned unmodified.

Classes along the inheritance tree have metadata attributes, codifying certain properties of them.
