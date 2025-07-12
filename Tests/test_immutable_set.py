import unittest

from concrete_classes import ImmutableSet


class TestTypedFrozenSet(unittest.TestCase):

    def test_init_and_content(self):
        fs = ImmutableSet(int, ['1', 2])
        self.assertEqual(fs.values, frozenset({1, 2}))

    def test_immutability(self):
        fs = ImmutableSet(str, ['a', 'b'])
        with self.assertRaises(AttributeError):
            fs.add('c')

    def test_map_filter(self):
        fs = ImmutableSet(int, [1, 2])
        self.assertEqual(fs.map(lambda x: x * 2), ImmutableSet(int, [2, 4]))
        self.assertEqual(fs.filter(lambda x: x > 1), ImmutableSet(int, [2]))

    def test_repr(self):
        fs = ImmutableSet(str, ['x'])
        self.assertIn("ImmutableSet<str>", repr(fs))


if __name__ == '__main__':
    unittest.main()
