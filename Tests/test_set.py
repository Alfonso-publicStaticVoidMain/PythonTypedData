import unittest

from concrete_classes import MutableSet, ImmutableSet, MutableList


class TestSet(unittest.TestCase):

    def test_basic_init(self):
        s = MutableSet(int, [1, '2', 2], coerce=True)
        self.assertEqual(s.values, {1, 2})

        fs = ImmutableSet(int, ['1', 2, '2'], coerce=True)
        self.assertEqual(fs.values, frozenset({1, 2}))

    def test_type_coercion(self):
        with self.assertRaises(TypeError):
            ImmutableSet(int, ['1', 2])

        self.assertEqual(ImmutableSet(int, ['1', 2], coerce=True).values, {1, 2})
        self.assertEqual(MutableSet(str, [2, '3'], coerce=True).values, {'2', '3'})
        self.assertEqual(MutableSet(str, [2, '3'], coerce=False).values, {'2', '3'})

    def test_immutability(self):
        fs = ImmutableSet(str, ['a', 'b'])
        with self.assertRaises(AttributeError):
            fs.add('c')

    def test_union_intersection(self):
        s1 = MutableSet(int, [1, 2])
        s2 = ImmutableSet(int, [2, 3])
        self.assertEqual(s1.union(s2).values, {1, 2, 3})
        self.assertEqual(s1.intersection(s2).values, {2})

        self.assertEqual(s1.union(s2, [3, 4], [4, 5]), MutableSet(values={1, 2, 3, 4, 5}))
        s3 = MutableSet(int, [1, '2', 3, 4, 5, 6, 7, 8], coerce=True)
        self.assertEqual(s3.intersection({0, 1, 2, 3, 4, '5'}, {'a': 2, 'b': 3, 'c': 4, 'd': 5, 'e': 6, 'f': 7, 'g': 8, 'h': 9}.values(), coerce=True), MutableSet(values={2, 3, 4, 5}))

    def test_difference_sym_dif(self):
        s1 = MutableSet(int, {1, 2, 3, 4})
        s2 = MutableSet(int, {2, 3, 4, 5})
        s3 = MutableSet(int, {1, 5, 6})
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
        s1 = MutableSet(str, {"a", 2, 3, "b"})
        s2 = MutableSet(str, {"a", "1"})
        s3 = MutableSet(str, {"a", "b"})
        s4 = ImmutableSet(str, {2, 3})
        s5 = ImmutableSet(int, {"2", "3"}, coerce=True)
        self.assertFalse(s2.is_subset(s1))
        self.assertEqual(s2.is_subset(s1), s1.is_superset(s2))

        self.assertTrue(s3.is_subset(s1))
        self.assertEqual(s3.is_subset(s1), s1.is_superset(s3))

        self.assertFalse(s5.is_subset(s1))
        self.assertEqual(s5.is_subset(s1), s1.is_superset(s5))

        self.assertFalse(s5.is_subset(s1))
        self.assertEqual(s5.is_subset(s1), s1.is_superset(s5))

        s6 = ImmutableSet(str, {"b", 2, 3, 4, "c"})
        self.assertFalse(s1.is_disjoint(s6))
        self.assertEqual(s1.is_disjoint(s6), s6.is_disjoint(s1))

        self.assertTrue(s4.is_disjoint(s3))
        self.assertEqual(s4.is_disjoint(s3), s3.is_disjoint(s4))

    def test_sub_super_set_coercion(self):
        int_st = MutableSet(int, {1, 2, 3})
        str_st = MutableSet(str, {'1', '2', '3'})
        self.assertTrue(int_st.is_subset(str_st, coerce=True))
        self.assertTrue(str_st.is_subset(int_st, coerce=True))

    def test_add_remove(self):
        s = MutableSet(str, ['a'])
        s.add('b')
        self.assertIn('a', s.values)
        self.assertIn('b', s.values)
        self.assertIn('a', s)
        self.assertIn('b', s)
        s.remove('a')
        self.assertNotIn('a', s.values)
        self.assertNotIn('a', s)
        self.assertNotIn(1, s)

        with self.assertRaises(KeyError):
            s.remove('c')

        s.discard('c')
        self.assertEqual(s, MutableSet(str, {'b'}))

    def test_update(self):
        mus = MutableSet(int, [-1, 0, 1, 2])
        mus.update([0, 1, 2, 3], [0, -1, -2, -3], ImmutableSet(int, [4, -4]), MutableSet(values=frozenset({0})))

        self.assertEqual(mus, MutableSet(int, [-4, -3, -2, -1, 0, 1, 2, 3, 4]))

        mus.difference_update([-4, 4], {3}, (-3,), {'a': 2}.values(), {-2: 'b'}.keys(), MutableSet(int, {0}))
        self.assertEqual(mus, MutableSet(int, [1, -1]))

    def test_intersection_sym_difference_update_multiple_types(self):
        s = MutableSet(int, [1, 2, 3, 4, 5])
        s.intersection_update(ImmutableSet(int, [2, 3, 6]), MutableList(int, [3, 4, 5, 6]), [3, 5, 7], {3, 5, 8})

        self.assertEqual(s.values, {3})

        mus = MutableSet(int, [1, 2, 3])
        ims = ImmutableSet(int, [2, 3, 4])
        mul = MutableList(int, [3, 4, 5])
        lst = [4, 5, 6]
        st = {5, 6, 7}
        mus.symmetric_difference_update(ims, mul, lst, st)

        self.assertEqual(mus.values, {1, 3, 4, 5, 7})

    def test_map_filter_flatmap(self):
        mus = MutableSet(int, [1, 2])
        self.assertEqual(mus.map(lambda x: x * 2), MutableSet(int, [2, 4]))
        self.assertEqual(mus.filter(lambda x: x > 1), MutableSet(int, [2]))
        self.assertEqual(mus.map(lambda x: x+1).filter(lambda x: x%2==0), MutableSet(int, [2]))
        self.assertEqual(mus.flatmap(lambda x : [x, -x]), MutableSet(int, {1, -1, 2, -2}))

        ims = ImmutableSet(int, [1, 2])
        self.assertEqual(ims.map(lambda x: x * 2), ImmutableSet(int, [2, 4]))
        self.assertEqual(ims.filter(lambda x: x > 1), ImmutableSet(int, [2]))
        self.assertEqual(ims.map(lambda x: x + 1).filter(lambda x: x % 2 == 0), ImmutableSet(int, [2]))
        self.assertEqual(ims.flatmap(lambda x: [x, -x]), ImmutableSet(int, {1, -1, 2, -2}))

    def test_length(self):
        s = MutableSet(str, [1, '1', 0, 0, 2])
        self.assertEqual(len(s), 3)
        s.add(1)
        self.assertEqual(len(s), 3)
        s.add('a')
        self.assertEqual(len(s), 4)

    def test_repr(self):
        mus = MutableSet(str, ['x', 'y'])
        self.assertIn("MutableSet<str>", repr(mus))

        ims = ImmutableSet(str, mus)
        self.assertIn("ImmutableSet<str>", repr(ims))

    def test_iter(self):
        values = {1, 2, 3, 4, 5}
        ims = ImmutableSet(int, values)
        for n in ims:
            self.assertTrue(n in values)

    def test_bool(self):
        s = MutableSet(str)
        self.assertFalse(s)

        s.add('a')
        self.assertTrue(s)


if __name__ == '__main__':
    unittest.main()
