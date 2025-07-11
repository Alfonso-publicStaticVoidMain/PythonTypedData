import unittest

from DataContainers import TypedTuple


class TestTypedTuple(unittest.TestCase):

    def test_init_and_access(self):
        tup = TypedTuple(int, ['1', 2])
        self.assertEqual(tup.values, (1, 2))
        self.assertEqual(tup[0], 1)

    def test_immutability(self):
        tup = TypedTuple(str, ['a', 'b'])
        error = False
        try:
            tup.values[0] = 'c'
        except TypeError:
            error = True
        self.assertTrue(error)


    def test_conversion(self):
        tup = TypedTuple(str, ['x', 'y'])
        self.assertEqual(tup.to_list(), ['x', 'y'])

    def test_repr_and_bool(self):
        tup = TypedTuple(str, ['x'])
        self.assertTrue(tup)
        self.assertIn("TypedTuple<str>", repr(tup))

    def test_map_filter_flatmap(self):
        tup = TypedTuple(int, [1, 2, 3])
        self.assertEqual(tup.map(lambda x: x + 1), TypedTuple(int, [2, 3, 4]))
        self.assertEqual(tup.filter(lambda x: x % 2), TypedTuple(int, [1, 3]))
        self.assertEqual(tup.flatmap(lambda x: [x, -x]), TypedTuple(int, [1, -1, 2, -2, 3, -3]))


if __name__ == '__main__':
    unittest.main()
