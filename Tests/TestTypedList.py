import unittest

from DataContainers import TypedList


class TestTypedList(unittest.TestCase):

    def test_empty_init(self):
        empty_list = TypedList(str)
        self.assertEqual(len(empty_list), 0)

    def test_type_coercion(self):
        lst = TypedList(int, ['1', 2])
        self.assertEqual(lst.values, [1, 2])

    def test_setitem_and_delitem(self):
        lst = TypedList(int, [1, 2, 3])
        lst[1] = 10
        self.assertEqual(lst.values, [1, 10, 3])

        lst[0:2] = [5, 6]
        self.assertEqual(lst.values, [5, 6, 3])

        del lst[2]
        self.assertEqual(lst.values, [5, 6])

    def test_init_and_get(self):
        int_lst = TypedList(int, ['0', 1, 2])
        str_lst = TypedList(str, ['a', 'b', 2, 0.4])

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
        lst = TypedList(int, [10, 2, 4])
        self.assertTrue(lst > TypedList(int, [9, 15, 27]))
        self.assertTrue(lst < TypedList(int, [10, 2, 5]))
        self.assertTrue(lst > [10, 1, 5])
        self.assertTrue(lst < (11, 100, 100))

    def test_add_substr_mul(self):
        self.assertEqual(TypedList(float, [0.1, 2, 0.3]) + [0.6, 1], TypedList(float, [0.1, 2, 0.3, 0.6, 1]))
        self.assertEqual(TypedList(int, [1, 2, 3, 4]) - [3, 4], TypedList(int, [1, 2]))
        self.assertEqual(TypedList(int, [0, 1] * 2), TypedList(int, [0, 1, 0, 1]))

    def test_contains_iter(self):
        values = ['zero', 'uno', 'dos', 'tres']
        lst = TypedList(str, values)
        self.assertTrue('zero' in lst)
        i = 0
        for s in lst:
            self.assertEqual(s, values[i])
            i+=1

    def test_sort(self):
        lst = TypedList(int, [5, 2, 9])
        lst.sort()
        self.assertEqual(lst.values, [2, 5, 9])

        lst.sort(reverse=True)
        self.assertEqual(lst.values, [9, 5, 2])

    def test_repr_and_bool(self):
        lst = TypedList(str, ['a', 'b'])
        self.assertTrue(lst)
        self.assertIn("TypedList<str>", repr(lst))

    def test_copy(self):
        lst = TypedList(int, [1, 2])
        new_lst = lst.copy()
        self.assertEqual(lst, new_lst)
        self.assertIsNot(lst, new_lst)

    def test_conversions(self):
        lst = TypedList(str, ['a', 'b'])
        self.assertEqual(lst.to_list(), ['a', 'b'])
        self.assertEqual(lst.to_tuple(), ('a', 'b'))
        self.assertEqual(lst.to_set(), {'a', 'b'})
        self.assertEqual(lst.to_frozen_set(), frozenset({'a', 'b'}))

    def test_count(self):
        lst = TypedList(int, [1, 2, 2, 3])
        self.assertEqual(lst.count(2), 2)

    def test_index(self):
        lst = TypedList(int, [10, 20, 30])
        self.assertEqual(lst.index(20), 1)

    def test_reversed(self):
        lst = TypedList(int, [1, 2, 3])
        self.assertEqual(list(reversed(lst)), [3, 2, 1])

    def test_sorted_method(self):
        lst = TypedList(str, ["b", "a", "c"])
        self.assertEqual(lst.sorted(), TypedList(str, ["a", "b", "c"]))
        self.assertEqual(lst.sorted(reverse=True), TypedList(str, ["c", "b", "a"]))

    def test_map_filter(self):
        lst = TypedList(int, [1, 2, 3])
        self.assertEqual(lst.map(lambda x: x * 2), TypedList(int, [2, 4, 6]))
        self.assertEqual(lst.filter(lambda x: x % 2 == 1), TypedList(int, [1, 3]))

    def test_flat_map(self):
        lst = TypedList(int, [1, 2])
        self.assertEqual(lst.flatmap(lambda x: [x, x + 10]), TypedList(int, [1, 11, 2, 12]))

    def test_for_each(self):
        acc = []
        lst = TypedList(str, ['a', 'b'])
        lst.for_each(lambda x: acc.append(x.upper()))
        self.assertEqual(acc, ['A', 'B'])

    def test_invalid_set_values(self):
        with self.assertRaises(TypeError):
            TypedList(int, {1, 2, 3})

    def test_invalid_append(self):
        lst = TypedList(int)
        with self.assertRaises(TypeError):
            lst.append("string")

    def test_invalid_setitem(self):
        lst = TypedList(int, [1, 2])
        with self.assertRaises(TypeError):
            lst[0] = "oops"

    def test_max_min(self):
        lst = TypedList(int, [1, 2, 5, 2])
        self.assertEqual(lst.max(), 5)
        self.assertIsNone(TypedList(int, []).max())

        self.assertEqual(lst.min(), 1)
        self.assertIsNone(TypedList(int, []).min())


if __name__ == '__main__':
    unittest.main()
