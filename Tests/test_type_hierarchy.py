import unittest
from typing import Any

from abstract_classes.abstract_sequence import AbstractSequence
from abstract_classes.abstract_set import AbstractSet
from abstract_classes.collection import Collection
from concrete_classes.list import MutableList
from concrete_classes.set import ImmutableSet
from type_validation.type_hierarchy import _is_subtype, _get_supertype


class TestGetSupertype(unittest.TestCase):

    def test_union_supertype(self):
        # int is subtype of int | str -> should return int | str
        self.assertEqual(_get_supertype(int, int | str), int | str)
        self.assertTrue(_is_subtype(int, int | str))
        self.assertTrue(_is_subtype(str, int | str))
        self.assertFalse(_is_subtype(str, int))

    def test_custom_class(self):
        class A:
            pass
        class B(A):
            pass
        class C(B):
            pass

        self.assertTrue(_is_subtype(C, B))
        self.assertTrue(_is_subtype(B, A))
        self.assertTrue(_is_subtype(C, A))
        self.assertFalse(_is_subtype(A, B))
        self.assertFalse(_is_subtype(A, C))
        self.assertEqual(_get_supertype(A, C), A)
        self.assertEqual(_get_supertype(A, B), A)
        self.assertEqual(_get_supertype(B, C), B)

    def test_commutative_for_known_subtype(self):
        self.assertEqual(
            _get_supertype(int, int | str),
            _get_supertype(int | str, int)
        )

    def test_union_vs_union(self):
        self.assertTrue(_is_subtype(str | int, int | str))
        self.assertTrue(_is_subtype(str | int, int | float | str))
        self.assertEqual(_get_supertype(int | str, int | str | float), int | str | float)

        class A:
            pass
        class B:
            pass
        class A_(A):
            pass
        class B_(B):
            pass
        class _A_(A):
            pass

        self.assertTrue(_is_subtype(A_ | B_, A | B))
        self.assertTrue(_is_subtype(A_ | _A_, A | B))
        self.assertTrue(_is_subtype(A_ | _A_, A))
        self.assertFalse(_is_subtype(A | B, A_ | B_))
        self.assertFalse(_is_subtype(A | B_, A_ | B))
        self.assertFalse(_is_subtype(A_ | B_, A_ | _A_))

    def test_any_as_top_type(self):
        self.assertEqual(_get_supertype(int, Any), Any)
        self.assertEqual(_get_supertype(Any, int), Any)
        self.assertTrue(_is_subtype(int, Any))
        self.assertFalse(_is_subtype(Any, int))  # invariant Any

        self.assertEqual(_get_supertype(int, int | Any), int | Any)
        self.assertTrue(_is_subtype(str, int | Any))

    def test_tuple(self):
        self.assertTrue(_is_subtype(tuple[int, ...], tuple[int | str, ...]))
        self.assertTrue(_is_subtype(tuple[int, int], tuple[int, ...]))
        self.assertFalse(_is_subtype(tuple[int, str], tuple[int, ...]))
        self.assertEqual(_get_supertype(tuple[int, ...], tuple[int | str, ...]), tuple[int | str, ...])
        self.assertTrue(_is_subtype(tuple[int, str], tuple[int, str]))
        self.assertFalse(_is_subtype(tuple[int, str], tuple[str, int]))

    def test_incompatible_origins(self):
        with self.assertRaises(TypeError):
            _get_supertype(list[int], set[int])
        with self.assertRaises(TypeError):
            _get_supertype(list[int], list[str])

    def test_collection_list_same_item_type(self):
        # List[int] extends Collection[int] -> should return Collection[int]
        self.assertEqual(_get_supertype(Collection[int], MutableList[int]), Collection[int])
        self.assertTrue(_is_subtype(MutableList[int], Collection[int]))
        self.assertFalse(_is_subtype(Collection[int], MutableList[int]))  # Collection not subtype of List

    def test_collection_list_wider_collection_type(self):
        # Collection[int | str] is supertype of List[int] -> should return Collection[int | str]
        self.assertEqual(_get_supertype(Collection[int | str], MutableList[int]), Collection[int | str])
        self.assertTrue(_is_subtype(MutableList[int], Collection[int | str]))

    def test_incompatible_collection_and_list(self):
        # Collection[int] and List[int | str] are incompatible
        with self.assertRaises(TypeError):
            _get_supertype(Collection[int], MutableList[int | str])

    def test_none_handling_in_union(self):
        # int should be subtype of int | None
        self.assertTrue(_is_subtype(int, int | None))
        # None should be subtype of int | None
        self.assertTrue(_is_subtype(None, int | None))
        # str is not subtype of int | None
        self.assertFalse(_is_subtype(str, int | None))
        self.assertEqual(
            _get_supertype(int, int | None),
            int | None
        )

    def test_unparameterized_type_against_parameterized(self):
        self.assertFalse(_is_subtype(list, list[int]))

    def test_nested_union_in_generics(self):
        self.assertEqual(_get_supertype(list[int], list[int | str]), list[int | str])
        class A:
            pass
        class B(A):
            pass
        self.assertEqual(_get_supertype(list[B], list[A | int | str]), list[A | int | str])
        self.assertEqual(_get_supertype(MutableList[B], AbstractSequence[A | int | str]), AbstractSequence[A | int | str])

    def test_deeply_nested_standard_types(self):
        t1 = list[dict[str, list[int]]]
        t2 = list[dict[str, list[int | str]]]
        result = _get_supertype(t1, t2)
        self.assertEqual(result, list[dict[str, list[int | str]]])
        self.assertTrue(_is_subtype(t1, result))
        self.assertTrue(_is_subtype(t2, result))
        # Check the deep mismatch is caught
        with self.assertRaises(TypeError):
            _get_supertype(list[dict[str, list[int]]], list[dict[str, set[int]]])

    def test_deeply_nested_custom_classes(self):
        t1 = MutableList[ImmutableSet[int]]
        t2 = AbstractSequence[AbstractSet[int | str]]
        # ImmutableSet[int] should be a subtype of AbstractSet[int | str]
        result = _get_supertype(t1, t2)
        self.assertEqual(result, AbstractSequence[AbstractSet[int | str]])
        self.assertTrue(_is_subtype(t1, result))
        self.assertTrue(_is_subtype(t2, result))
        # Incompatible element types at inner-most level should raise
        bad_t1 = MutableList[ImmutableSet[int]]
        bad_t2 = AbstractSequence[AbstractSet[str]]
        with self.assertRaises(TypeError):
            _get_supertype(bad_t1, bad_t2)


if __name__ == '__main__':
    unittest.main()
