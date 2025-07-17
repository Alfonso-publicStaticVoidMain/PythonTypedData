import unittest
from collections import namedtuple

from abstract_classes import Collection
from concrete_classes import MutableList, ImmutableList


class TestList(unittest.TestCase):

    def test_class_name(self):
        lst = MutableList[int]([0, 1, 2])
        class_name = type(lst).__name__
        self.assertEqual(class_name, "MutableList")

    def test_init_and_access(self):
        iml = ImmutableList[int](['1', 2], coerce=True)
        self.assertEqual(iml.values, (1, 2))
        self.assertEqual(iml[0], 1)

        mul = MutableList[int](iml)
        self.assertEqual(list(iml.values), mul.values)
        self.assertEqual(iml.values, tuple(mul.values))

        mul_2 = MutableList.of(iml)
        self.assertEqual(mul, mul_2)

    def test_partial_init_parameters(self):
        with self.assertRaises(TypeError):
            MutableList([1, 2, 3])
        mul = MutableList.of([1, 2, 3])
        self.assertEqual(mul.item_type, int)

        iml = ImmutableList.of([1, 2, '3'])
        self.assertEqual(iml.item_type, int | str)

        empty_list = MutableList.empty(str)
        self.assertEqual(len(empty_list), 0)
        self.assertFalse(empty_list)

    def test_type_coercion(self):
        lst = MutableList[int](['1', 2], coerce=True)
        self.assertEqual(lst.values, [1, 2])

        iml = ImmutableList[float]([1, 2.25], coerce=False)
        self.assertEqual(iml.values, (1.0, 2.25))
        self.assertEqual(iml[0], 1)

        with self.assertRaises(TypeError):
            mul = MutableList[int]([1, 2, '3'], coerce=False)

    def test_immutability(self):
        iml = ImmutableList[str](['a', 'b'])
        with self.assertRaises(TypeError):
            iml[0] = 'c'
        with self.assertRaises(TypeError):
            iml.values[0] = 'c'

    def test_setitem_and_delitem(self):
        lst = MutableList[int]([1, 2, 3])
        lst[1] = 10
        self.assertEqual(lst.values, [1, 10, 3])

        lst[0:2] = [5, 6]
        self.assertEqual(lst.values, [5, 6, 3])

        del lst[2]
        self.assertEqual(lst.values, [5, 6])

    def test_init_and_get(self):
        int_lst = MutableList[int]([0, 1, 2])
        str_lst = MutableList[str](['a', 'b', 2, 0.4], coerce=True)

        self.assertEqual(int_lst[0], 0)
        self.assertEqual(int_lst[1], 1)
        self.assertEqual(int_lst[2], 2)

        self.assertEqual(str_lst[0], 'a')
        self.assertEqual(str_lst[1], 'b')
        self.assertEqual(str_lst[2], '2')
        self.assertNotEqual(str_lst[2], 2)
        self.assertEqual(str_lst[3], '0.4')
        self.assertNotEqual(str_lst[3], 0.4)

    def test_comparisons(self):
        lst = MutableList([10, 2, 4], int)

        self.assertTrue(lst > MutableList([9, 15, 27], int))
        self.assertTrue(lst < MutableList([10, 2, 5], int))

        self.assertTrue(lst > ImmutableList([9, 15, 27], int))
        self.assertTrue(lst < ImmutableList([10, 2, 5], int))

        self.assertTrue(lst <= lst)
        self.assertTrue(lst >= ImmutableList(lst, int))

        self.assertTrue(lst > [10, 1, 5])
        self.assertTrue(lst < (11, 100, 100))

    def test_add_substr_mul(self):
        self.assertEqual(MutableList([0.1, 2, 0.3], float) + [0.6, 1], MutableList([0.1, 2, 0.3, 0.6, 1], float))
        self.assertEqual(MutableList([1, 2, 3, 4], int) - [3, 4], MutableList([1, 2], int))
        self.assertEqual(MutableList([0, 1] * 2, int), MutableList([0, 1, 0, 1], int))

    def test_contains_iter(self):
        values = ['zero', 'uno', 'dos', 'tres']
        lst = MutableList(values, str)
        self.assertTrue('zero' in lst)
        i = 0
        for s in lst:
            self.assertEqual(s, values[i])
            i+=1

    def test_sort_and_sorted(self):
        lst = MutableList([5, 2, 9], int)
        lst.sort()
        self.assertEqual(lst.values, [2, 5, 9])

        lst.sort(reverse=True)
        self.assertEqual(lst.values, [9, 5, 2])

        iml = ImmutableList(lst, int)
        self.assertEqual(iml.sorted().values, (2, 5, 9))
        self.assertEqual(iml.sorted(reverse=True).values, (9, 5, 2))

    def test_repr_and_bool(self):
        mul = MutableList(['a', 'b'], str)
        self.assertTrue(mul)
        self.assertIn("MutableList<str>", repr(mul))

        iml = ImmutableList(['x'], str)
        self.assertTrue(iml)
        self.assertIn("ImmutableList<str>", repr(iml))

        empty_lst = MutableList(item_type=int)
        self.assertFalse(empty_lst)

        empty_imlist = ImmutableList(item_type=str)
        self.assertFalse(empty_imlist)

    def test_copy(self):
        lst = MutableList([1, 2], int)
        new_lst = lst.copy()
        self.assertEqual(lst, new_lst)
        self.assertIsNot(lst, new_lst)

    def test_conversions(self):
        lst = MutableList(['a', 'b'], str)
        self.assertEqual(lst.to_list(), ['a', 'b'])
        self.assertEqual(lst.to_tuple(), ('a', 'b'))
        self.assertEqual(lst.to_set(), {'a', 'b'})
        self.assertEqual(lst.to_frozen_set(), frozenset({'a', 'b'}))

    def test_count(self):
        lst = MutableList([1, 2, 2, 3], int)
        self.assertEqual(lst.count(2), 2)
        self.assertEqual(lst.count(1), 1)
        self.assertEqual(lst.count(3), 1)

    def test_index(self):
        lst = MutableList([10, 20, 30], int)
        self.assertEqual(lst.index(20), 1)

    def test_reversed(self):
        lst = MutableList([1, 2, 3], int)
        self.assertEqual(list(reversed(lst)), [3, 2, 1])

    def test_sorted_methods(self):
        lst = MutableList(["b", "a", "c"], str)
        self.assertEqual(lst.sorted(), MutableList(["a", "b", "c"], str))
        self.assertEqual(lst.sorted(reverse=True), MutableList(["c", "b", "a"], str))

    def test_map_filter_flatmap(self):
        lst = MutableList([1, 2, 3], int)
        self.assertEqual(lst.map(lambda x: x * 2), MutableList([2, 4, 6], int))
        self.assertEqual(lst.filter(lambda x: x % 2 == 1), MutableList([1, 3], int))
        self.assertEqual(lst.flatmap(lambda x: [x, x + 10]), MutableList([1, 11, 2, 12, 3, 13], int))

        iml = ImmutableList([1, 2, 3], int)
        self.assertEqual(iml.map(lambda x: x + 1), ImmutableList([2, 3, 4], int))
        self.assertEqual(iml.filter(lambda x: x % 2), ImmutableList([1, 3], int))
        self.assertEqual(iml.flatmap(lambda x: [x, -x]), ImmutableList([1, -1, 2, -2, 3, -3], int))

    def test_any_all_none_match(self):
        iml = ImmutableList([1, 2, 3, 4, 6, 12], int)
        self.assertTrue(iml.all_match(lambda n: 12 % n == 0))
        self.assertFalse(iml.any_match(lambda n: n < 0))
        self.assertTrue(iml.none_match(lambda n: n < 0))

    def test_reduce(self):
        mul = MutableList([0, 1, 2, 3], int)
        self.assertEqual(mul.reduce(lambda x, y: x + y), 6)

        self.assertEqual(ImmutableList(item_type=int).reduce(lambda x, y: x + y, 0), 0)

        str_lst = ImmutableList(['J', 'A', 'V', 'A'], str)
        self.assertEqual(str_lst.reduce(lambda s1, s2: s1 + s2, '_'), '_JAVA')

    def test_for_each(self):
        acc = []
        lst = MutableList(['a', 'b'], str)
        lst.for_each(lambda x: acc.append(x.upper()))
        self.assertEqual(acc, ['A', 'B'])

    def test_invalid_set_values(self):
        with self.assertRaises(TypeError):
            MutableList({1, 2, 3}, int)

    def test_invalid_append(self):
        lst = MutableList(item_type=int)
        with self.assertRaises(TypeError):
            lst.append("string")

    def test_append(self):
        int_lst = MutableList(item_type=int)
        int_lst.append('0', coerce=True)
        self.assertEqual(int_lst[0], 0)
        with self.assertRaises(TypeError):
            int_lst.append('1', coerce=False)

        str_lst = MutableList(item_type=str)
        str_lst.append(0, coerce=True)
        str_lst.append(1, coerce=False)
        self.assertEqual(str_lst[0], '0')
        self.assertEqual(str_lst[1], '1')

    def test_invalid_setitem(self):
        lst = MutableList([1, 2], int)
        with self.assertRaises(TypeError):
            lst[0] = "oops"

    def test_max_min(self):
        lst = MutableList([1, 2, 5, 2], int)
        self.assertEqual(lst.max(), 5)
        self.assertIsNone(MutableList([], int).max())

        self.assertEqual(lst.min(), 1)
        self.assertIsNone(MutableList([], int).min())

    def test_distinct(self):
        mul = MutableList(['a', 'a', 'b', 'b', 'b', 'c'], str).distinct()
        other_mul = MutableList[str](['a', 'b', 'c'])
        equality = Collection.__eq__(mul, other_mul)
        self.assertEqual(mul, other_mul)

        STR_INT = namedtuple("STR_INT", ["string", "integer"])
        iml = ImmutableList([STR_INT('a', 1), STR_INT('b', 2), STR_INT('c', 1)], STR_INT)
        self.assertEqual(iml.distinct(lambda tup: tup.integer),
                         ImmutableList([STR_INT('a', 1), STR_INT('b', 2)], STR_INT))

    def test_collect(self):
        mul = MutableList([1, 2, 3, 4, 5], int)
        dic = mul.collect(
            supplier=lambda:{},
            accumulator=lambda d, n: d.__setitem__(n, 2**n),
            finisher=lambda d: d | {0: 1}
        )
        self.assertEqual(dic, {0: 1, 1: 2, 2: 4, 3: 8, 4: 16, 5: 32})

if __name__ == '__main__':
    unittest.main()
