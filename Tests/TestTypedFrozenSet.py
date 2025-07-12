import unittest

from DataContainers import TypedFrozenSet


class TestTypedFrozenSet(unittest.TestCase):

    def test_init_and_content(self):
        fs = TypedFrozenSet(int, ['1', 2])
        self.assertEqual(fs.values, frozenset({1, 2}))

    def test_immutability(self):
        fs = TypedFrozenSet(str, ['a', 'b'])
        with self.assertRaises(AttributeError):
            fs.add('c')

    def test_map_filter(self):
        fs = TypedFrozenSet(int, [1, 2])
        self.assertEqual(fs.map(lambda x: x * 2), TypedFrozenSet(int, [2, 4]))
        self.assertEqual(fs.filter(lambda x: x > 1), TypedFrozenSet(int, [2]))

    def test_repr(self):
        fs = TypedFrozenSet(str, ['x'])
        self.assertIn("TypedFrozenSet<str>", repr(fs))


if __name__ == '__main__':
    unittest.main()
