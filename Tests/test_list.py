import unittest


from concrete_classes.list import MutableList, ImmutableList
from concrete_classes.set import ImmutableSet


class TestList(unittest.TestCase):

    def test_multiple_value_init(self):
        lst = MutableList[str]('a', 'b', 'c', 1, _coerce=True)
        lst_2 = MutableList[str](['a', 'b', 'c', 1], _coerce=True)
        self.assertEqual(lst, lst_2)

    def test_class_name(self):
        from abstract_classes.generic_base import class_name
        lst = MutableList[int]([0, 1, 2])
        self.assertEqual(class_name(type(lst)), "MutableList[int]")

        iml = ImmutableList.of('a', 2, 0.1)
        self.assertEqual(class_name(type(iml)), "ImmutableList[int | str | float]")

    def test_init_and_access(self):
        iml = ImmutableList[int](['1', 2], _coerce=True)
        self.assertEqual(iml.values, (1, 2))
        self.assertEqual(iml[0], 1)

        mul = MutableList[int](iml)
        self.assertEqual(list(iml.values), mul.values)
        self.assertEqual(iml.values, tuple(mul.values))

        mul_2 = MutableList.of(iml)
        self.assertEqual(mul, mul_2)

    def test_partial_init_parameters(self):
        # Creating a list without the type parameter [...] raises a TypeError
        with self.assertRaises(TypeError):
            mul = MutableList([1, 2, 3])
        # To automatically infer the type, use the .of method
        mul = MutableList.of([1, 2, 3])
        self.assertEqual(mul.item_type, int)

        # Inferring the type from a mixed list gets a UnionType
        iml = ImmutableList.of([1, 2, '3'])
        self.assertEqual(iml.item_type, int | str)

        empty_list = MutableList[str].empty()
        self.assertEqual(len(empty_list), 0)
        self.assertFalse(empty_list)

    def test_type_coercion(self):
        # '1' is coerced to int when _coerce parameter is set to True
        lst = MutableList[int](['1', 2], _coerce=True)
        self.assertEqual(lst.values, [1, 2])

        # 1 is coerced to float even when _coerce parameter is False
        iml = ImmutableList[float]([1, 2.25], _coerce=False)
        self.assertEqual(iml.values, (1.0, 2.25))
        # This is because Python considers it equal to both the int and a float representation of 1
        self.assertEqual(iml[0], 1)
        self.assertEqual(iml[0], 1.0)

        # '3' is not coerced to int if _coerce parameter is False, and a TypeError is raised.
        with self.assertRaises(TypeError):
            mul = MutableList[int]([1, 2, '3'], _coerce=False)

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
        str_lst = MutableList[str](['a', 'b', 2, 0.4], _coerce=True)

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
        lst = MutableList[int]([10, 2, 4])

        self.assertTrue(lst > MutableList[int]([9, 15, 27]))
        self.assertTrue(lst < MutableList[int]([10, 2, 5]))

        self.assertTrue(lst > ImmutableList[int]([9, 15, 27]))
        self.assertTrue(lst < ImmutableList[int]([10, 2, 5]))

        self.assertTrue(lst <= lst)
        self.assertTrue(lst >= ImmutableList[int](lst))
        self.assertFalse(lst < lst)
        self.assertFalse(ImmutableList[int](lst) > lst)

        self.assertTrue(lst > MutableList[int]((10, 1, 5)))
        self.assertTrue(lst < MutableList[int]([11, 100, 100]))

    def test_add_mul(self):
        self.assertEqual(MutableList[float]([0.1, 2, 0.3]) + MutableList[float]([0.6, 1]), MutableList[float]([0.1, 2, 0.3, 0.6, 1]))
        self.assertEqual(MutableList[int]([0, 1]) * 2, MutableList[int]([0, 1, 0, 1]))

    def test_contains_iter(self):
        values = ['zero', 'uno', 'dos', 'tres']
        lst = MutableList[str](values)
        self.assertTrue('zero' in lst)
        i = 0
        for s in lst:
            self.assertEqual(s, values[i])
            i+=1

    def test_sort_and_sorted(self):
        lst = MutableList[int](5, 2, 9)
        lst.sort()
        self.assertEqual(lst.values, [2, 5, 9])

        lst.sort(reverse=True)
        self.assertEqual(lst.values, [9, 5, 2])

        iml = ImmutableList[int](lst)
        self.assertEqual(iml.sorted().values, (2, 5, 9))
        self.assertEqual(iml.sorted(reverse=True).values, (9, 5, 2))

    def test_conversions(self):
        lst = MutableList[str]('a', 'b')
        self.assertEqual(lst.to_list(), ['a', 'b'])
        self.assertEqual(lst.to_tuple(), ('a', 'b'))
        self.assertEqual(lst.to_set(), {'a', 'b'})
        self.assertEqual(lst.to_frozen_set(), frozenset({'a', 'b'}))

    def test_count(self):
        lst = MutableList[int](1, 2, 2, 3)
        self.assertEqual(lst.count(2), 2)
        self.assertEqual(lst.count(1), 1)
        self.assertEqual(lst.count(3), 1)

    def test_index(self):
        lst = MutableList[int](10, 20, 30)
        self.assertEqual(lst.index(20), 1)

    def test_reversed(self):
        lst = MutableList[int](1, 2, 3)
        self.assertEqual(list(reversed(lst)), [3, 2, 1])

    def test_sorted_methods(self):
        lst = MutableList[str]("b", "a", "c")
        self.assertEqual(lst.sorted(), MutableList[str]("a", "b", "c"))
        self.assertEqual(lst, MutableList[str]("b", "a", "c"))
        self.assertEqual(lst.sorted(reverse=True), MutableList[str]("c", "b", "a"))

    def test_inplace_sort_reverse(self):
        mul = MutableList[str]('a', 'x', 'b')
        mul.sort()
        self.assertEqual(mul, MutableList.of('a', 'b', 'x'))
        mul.append('c')
        mul.sort(reverse=True)
        self.assertEqual(mul, MutableList.of('x', 'c', 'b', 'a'))
        mul.append('y')
        mul.reverse()
        self.assertEqual(mul, MutableList.of('y', 'a', 'b', 'c', 'x'))


    def test_invalid_set_values(self):
        with self.assertRaises(TypeError):
            MutableList[int]({1, 2, 3})

    def test_invalid_append(self):
        lst = MutableList[int]()
        with self.assertRaises(TypeError):
            lst.append("string")

    def test_append(self):
        int_lst = MutableList[int]()
        # '0' is safely coerced to int when _coerce = True
        int_lst.append('0', _coerce=True)
        self.assertEqual(int_lst[0], 0)
        # '1' won't be coerced to int when _coerce = False
        with self.assertRaises(TypeError):
            int_lst.append('1', _coerce=False)

        # 0 and 1 will be coerced to str no matter if _coerce is set to True or not.
        str_lst = MutableList[str]()
        str_lst.append(0, _coerce=True)
        str_lst.append(1, _coerce=False)
        self.assertEqual(str_lst[0], '0')
        self.assertEqual(str_lst[1], '1')

    def test_invalid_setitem(self):
        lst = MutableList[int](1, 2)
        with self.assertRaises(TypeError):
            lst[0] = "oops"

    def test_distinct(self):
        mul = MutableList[str]('a', 'a', 'b', 'b', 'b', 'c').distinct()
        other_mul = MutableList[str]('a', 'b', 'c')
        self.assertEqual(mul, other_mul)

        iml = ImmutableList[tuple[str, int]](('a', 1), ('b', 2), ('c', 1))
        self.assertEqual(iml.distinct(lambda tup: tup[1]), ImmutableList.of(('a', 1), ('b', 2)))

    def test_in_place_add_mul_sub(self):
        mul = MutableList[str]('a')
        mul += ImmutableList[str]('b')
        self.assertEqual(mul, MutableList[str]('a', 'b'))

        mul += ['c']
        self.assertEqual(mul, MutableList[str]('a', 'b', 'c'))

        mul += ('d',)
        self.assertEqual(mul, MutableList[str]('a', 'b', 'c', 'd'))

        mul = MutableList[str]('a')
        mul *= 3
        self.assertEqual(mul, MutableList[str]('a', 'a', 'a'))

        with self.assertRaises(TypeError):
            mul *= 'c'

    def test_inplace_filter(self):
        mul = MutableList[str]('a', 'b', 'abc')
        mul.filter_inplace(lambda s : s.startswith('a'))
        self.assertEqual(mul, MutableList[str]('a', 'abc'))

        mul.replace('abc', 123)
        self.assertEqual(mul, MutableList.of('a', '123'))
        self.assertNotEqual(mul, MutableList.of('a', 123))

        mul.map_inplace(lambda s : s[0])
        self.assertEqual(mul, MutableList.of('a', '1'))

        mul.replace_many({'a' : 'b', '1' : 2})
        self.assertEqual(mul, MutableList.of('b', '2'))

if __name__ == '__main__':
    unittest.main()
