A recreation of Java's Collection and Map interfaces within Python.

The base class for the inheritance tree is GenericBase\[*Ts\], a generic class accepting a TypedVarTuple, which adds the behaviour of storing the generic types given to the class with its implementation of \_\_class\_getitem\_\_ as a class attribute \_args.

Inheriting directly from GenericBase we have Collection\[T\] and AbstractDict\[K, V\], which implement an \_\_init\_\_ method following the logic for instantiating their subclasses. This two can't be instantiated directly, and calling their new method will raise a TypeError.

Inheriting from Collection\[T\] we have AbstractSequence\[T\] and AbstractSet\[T\], and from each of those, AbstractMutableSequence\[T\] and AbstractMutableSet\[T\]. Inheriting from AbstractDict\[K, V\] we have AbstractMutableDict\[K, V\]. Each of those classes is still treated as abstract and impossible to instantiate directly.

Finally, the concrete classes included are MutableList\[T\], extending AbstractMutableSequence\[T\], ImmutableList\[T\], extending AbstractSequence\[T\], MutableSet\[T\], extending AbstractMutableSet\[T\], ImmutableSet, extending AbstractSet\[T\], MutableDict\[K, V\], extending AbstractMutableDict\[K, V\], and ImmutableDict\[K, V\], extending AbstractDict\[K, V\].
