import unittest

from abstract_classes import AbstractSet, Collection
from concrete_classes import MutableSet, ImmutableSet, MutableList, ImmutableList


class TestSet(unittest.TestCase):

    def test_basic_init(self):
        mus = MutableSet[int](1, '2', 2, _coerce=True)
        self.assertEqual(mus.values, {1, 2})

        ims = ImmutableSet[int]('1', 2, '2', _coerce=True)
        self.assertEqual(ims.values, frozenset({1, 2}))

    def test_type_coercion(self):
        with self.assertRaises(TypeError):
            ImmutableSet[int]('1', 2)

        self.assertEqual(ImmutableSet[int]('1', 2, _coerce=True).values, {1, 2})
        self.assertEqual(MutableSet[str](2, '3', _coerce=True).values, {'2', '3'})
        self.assertEqual(MutableSet[str](2, '3', _coerce=False).values, {'2', '3'})

    def test_immutability(self):
        ims = ImmutableSet[str]('a', 'b')
        with self.assertRaises(AttributeError):
            ims.add('c')

    def test_union_intersection(self):
        s1 = MutableSet[int](1, 2)
        s2 = ImmutableSet[int](2, 3)
        self.assertEqual(s1.union(s2).values, {1, 2, 3})
        self.assertEqual(s1.union(s2), s2.union(s1))
        self.assertEqual(s1.intersection(s2).values, {2})
        self.assertEqual(s1.intersection(s2), s2.intersection(s1))

        self.assertEqual(
            s1.union(s2, [3, 4], [4, 5]),
            MutableSet[int](1, 2, 3, 4, 5)
        )

        s3 = MutableSet[int](1, '2', 3, 4, 5, 6, 7, 8, _coerce=True)
        self.assertEqual(
            s3.intersection(
                {0, 1, 2, 3, 4, '5'},
                {'a': 2, 'b': 3, 'c': 4, 'd': 5, 'e': 6, 'f': 7, 'g': 8, 'h': 9}.values(),
                _coerce=True
            ),
            MutableSet[int](2, 3, 4, 5)
        )

    def test_difference_sym_dif(self):
        s1 = MutableSet[int](1, 2, 3, 4)
        s2 = MutableSet[int](2, 3, 4, 5)
        s3 = MutableSet[int](1, 5, 6)
        lst = [6, 7]
        st = {7, 8}

        self.assertEqual(s1.difference(s2).values, {1})
        self.assertEqual(s1.symmetric_difference(s2), s2.symmetric_difference(s1))
        self.assertEqual(s1.symmetric_difference(s2).values, {1, 5})
        self.assertEqual(s1.symmetric_difference(s2, s3, lst, st).values, {8})
        self.assertEqual(
            s1.symmetric_difference(s2).symmetric_difference(s3),
            s1.symmetric_difference(s2.symmetric_difference(s3))
        )

    def test_sub_super_set_disjoint(self):
        s1 = MutableSet[str]("a", 2, 3, "b")
        s2 = MutableSet[str]("a", "1")
        s3 = MutableSet[str]("a", "b")
        s4 = ImmutableSet[str](2, 3)
        s5 = ImmutableSet[int]("2", "3", _coerce=True)

        self.assertFalse(s2.is_subset(s1))
        self.assertEqual(s2.is_subset(s1), s1.is_superset(s2))

        self.assertTrue(s3.is_subset(s1))
        self.assertEqual(s3.is_subset(s1), s1.is_superset(s3))

        self.assertFalse(s5.is_subset(s1))
        self.assertEqual(s5.is_subset(s1), s1.is_superset(s5))

        s6 = ImmutableSet[str]("b", 2, 3, 4, "c")
        self.assertFalse(s1.is_disjoint(s6))
        self.assertEqual(s1.is_disjoint(s6), s6.is_disjoint(s1))

        self.assertTrue(s4.is_disjoint(s3))
        self.assertEqual(s4.is_disjoint(s3), s3.is_disjoint(s4))

    def test_sub_super_set_coercion(self):
        int_st = MutableSet[int](1, 2, 3)
        str_st = MutableSet[str]('1', '2', '3')
        self.assertTrue(int_st.is_subset(str_st, _coerce=True))
        self.assertTrue(str_st.is_subset(int_st, _coerce=True))

    def test_add_remove(self):
        s = MutableSet[str]('a')
        s.add('b')
        self.assertIn('a', s)
        self.assertIn('b', s)
        s.remove('a')
        self.assertNotIn('a', s)
        self.assertNotIn(1, s)

        with self.assertRaises(KeyError):
            s.remove('c')

        s.discard('c')
        self.assertEqual(s, MutableSet[str]('b'))

    def test_update(self):
        mus = MutableSet[int](0, 1)
        mus.update([2, 3], MutableList.of(4, 5))

        self.assertEqual(mus, MutableSet[int](0, 1, 2, 3, 4, 5))

        mus_2 = MutableSet.of(0, 1, 2, 3, 4, 5, 6, 7, 8)
        mus_2.difference_update([1, 3], {5, 27, 33}, MutableSet[int](-1, -3, 7))
        self.assertEqual(mus_2, MutableSet[int](0, 2, 4, 6, 8))

    def test_intersection_sym_difference_update_multiple_types(self):
        s = MutableSet[int](1, 2, 3, 4, 5)
        s.intersection_update(
            ImmutableSet[int](2, 3, 6),
            MutableList[int](3, 4, 5),
            [3, 5, 7],
            {3, 5, 8}
        )
        self.assertEqual(s.values, {3})

        mus = MutableSet[int](1, 2, 3)
        ims = ImmutableSet[int](2, 3, 4)
        mul = MutableList[int](3, 4, 5)
        lst = [4, 5, 6]
        st = {5, 6, 7}
        mus.symmetric_difference_update(ims, mul, lst, st)

        self.assertEqual(mus.values, {1, 3, 4, 5, 7})

    def test_length(self):
        s = MutableSet[str](1, '1', 0, 0, 2)
        self.assertEqual(len(s), 3)
        s.add(1)
        self.assertEqual(len(s), 3)
        s.add('a')
        self.assertEqual(len(s), 4)

    def test_iter(self):
        values = {1, 2, 3, 4, 5}
        ims = ImmutableSet[int](*values)
        for n in ims:
            self.assertIn(n, values)

    def test_in_place_updates(self):
        st = MutableSet[int](0)
        st |= ImmutableSet[int](0, 1, 2, 3) # Union = {0, 1, 2, 3}
        self.assertEqual(st, MutableSet[int](0, 1, 2, 3))

        st &= {2, 3} # Intersection = {2, 3}
        self.assertEqual(st, MutableSet[int](2, 3))

        st -= frozenset({3, 4}) # Difference = {2}
        self.assertEqual(st, MutableSet[int](2))

        st ^= {2, 0} # Symmetric Difference = {0}
        self.assertEqual(st, MutableSet[int](0))


if __name__ == '__main__':
    unittest.main()
