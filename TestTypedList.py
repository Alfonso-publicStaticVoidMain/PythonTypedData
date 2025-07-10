import unittest

from DataContainers import TypedList


class TestTypedList(unittest.TestCase):

    def test_empty_init(self):
        empty_list = TypedList(str)
        self.assertEqual(len(empty_list), 0)

    def test_type_coercion(self):
        my_list = TypedList(int, ['1', 2])
        self.assertEqual(my_list.values, [1, 2])

    def test_setitem_and_delitem(self):
        lst = TypedList(int, [1, 2, 3])
        lst[1] = 10
        self.assertEqual(lst.values, [1, 10, 3])

        lst[0:2] = [5, 6]
        self.assertEqual(lst.values, [5, 6, 3])

        del lst[2]
        self.assertEqual(lst.values, [5, 6])

    def test_append(self):
        my_int_list = TypedList(int, [0, 1, 2])
        my_int_list.append(3)
        my_int_list.append('4')
        error = False
        try:
            my_int_list.append('aaaaa')
        except TypeError:
            error = True
        self.assertListEqual(my_int_list.values, [0, 1, 2, 3, 4])
        self.assertTrue(error)

    def test_init_and_get(self):
        my_int_list = TypedList(int, ['0', 1, 2])
        my_str_list = TypedList(str, ['a', 'b', 2, 0.4])

        self.assertEqual(my_int_list[0], 0)
        self.assertEqual(my_int_list[1], 1)
        self.assertEqual(my_int_list[2], 2)

        self.assertEqual(my_str_list[0], 'a')
        self.assertEqual(my_str_list[1], 'b')
        self.assertEqual(my_str_list[2], '2')
        self.assertEqual(my_str_list[3], '0.4')

    def test_comparisons(self):
        my_int_list = TypedList(int, [10, 2, 4])
        self.assertTrue(my_int_list > TypedList(int, [9, 15, 27]))
        self.assertTrue(my_int_list < TypedList(int, [10, 2, 5]))
        self.assertTrue(my_int_list > [10, 1, 5])
        self.assertTrue(my_int_list < (11, 100, 100))

    def test_add_substr_mul(self):
        self.assertEqual(TypedList(float, [0.1, 2, 0.3]) + [0.6, 1], TypedList(float, [0.1, 2, 0.3, 0.6, 1]))
        self.assertEqual(TypedList(int, [1, 2, 3, 4]) - [3, 4], TypedList(int, [1, 2]))
        self.assertEqual(TypedList(int, [0, 1] * 2), TypedList(int, [0, 1, 0, 1]))

    def test_contains_iter(self):
        values = ['zero', 'uno', 'dos', 'tres']
        my_str_list = TypedList(str, values)
        self.assertTrue('zero' in my_str_list)
        i = 0
        for s in my_str_list:
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


if __name__ == '__main__':
    unittest.main()
