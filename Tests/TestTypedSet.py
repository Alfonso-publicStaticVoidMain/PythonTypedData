import unittest

from DataContainers import MutableSet


class TestTypedSet(unittest.TestCase):

    def test_basic_init(self):
        s = MutableSet(int, [1, '2', 2])
        self.assertEqual(s.values, {1, 2})

    def test_union_intersection(self):
        s1 = MutableSet(int, [1, 2])
        s2 = MutableSet(int, [2, 3])
        self.assertEqual(s1.union(s2).values, {1, 2, 3})
        self.assertEqual(s1.intersection(s2).values, {2})

    def test_difference_sym_dif(self):
        s1 = MutableSet(int, {1, 2, 3, 4})
        s2 = MutableSet(int, {2, 3, 4, 5})
        self.assertEqual(s1.difference(s2).values, {1})
        self.assertEqual(s1.symmetric_difference(s2), s2.symmetric_difference(s1))
        self.assertEqual(s1.symmetric_difference(s2).values, {1, 5})

    def test_sub_super_set_disjoint(self):
        s1 = MutableSet(str, {"a", 2, 3, "b"})
        s2 = MutableSet(str, {"a", "1"})
        s3 = MutableSet(str, {"a", "b"})
        s4 = MutableSet(str, {2, 3})
        s5 = MutableSet(int, {"2", "3"})
        self.assertFalse(s2.is_subset(s1))
        self.assertEqual(s2.is_subset(s1), s1.is_superset(s2))

        self.assertTrue(s3.is_subset(s1))
        self.assertEqual(s3.is_subset(s1), s1.is_superset(s3))

        self.assertFalse(s5.is_subset(s1))
        self.assertEqual(s5.is_subset(s1), s1.is_superset(s5))

        self.assertFalse(s5.is_subset(s1))
        self.assertEqual(s5.is_subset(s1), s1.is_superset(s5))

        s6 = MutableSet(str, {"b", 2, 3, 4, "c"})
        self.assertFalse(s1.is_disjoint(s6))
        self.assertEqual(s1.is_disjoint(s6), s6.is_disjoint(s1))

        self.assertTrue(s4.is_disjoint(s3))
        self.assertEqual(s4.is_disjoint(s3), s3.is_disjoint(s4))

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

    def test_map_filter(self):
        s = MutableSet(int, [1, 2])
        self.assertEqual(s.map(lambda x: x * 2), MutableSet(int, [2, 4]))
        self.assertEqual(s.filter(lambda x: x > 1), MutableSet(int, [2]))
        self.assertEqual(s.map(lambda x: x+1).filter(lambda x: x%2==0), MutableSet(int, [2]))

    def test_length(self):
        s = MutableSet(str, [1, '1', 0, 0, 2])
        self.assertEqual(len(s), 3)
        s.add(1)
        self.assertEqual(len(s), 3)
        s.add('a')
        self.assertEqual(len(s), 4)

    def test_repr(self):
        s = MutableSet(str, ['x', 'y'])
        self.assertIn("MutableSet<str>", repr(s))


if __name__ == '__main__':
    unittest.main()
