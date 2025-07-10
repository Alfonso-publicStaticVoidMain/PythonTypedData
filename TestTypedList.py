import unittest

from DataContainers import TypedList


class MyTestCase(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()
