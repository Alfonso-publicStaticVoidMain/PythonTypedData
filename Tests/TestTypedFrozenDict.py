import unittest

from frozendict import frozendict
from DataContainers import TypedFrozenDict


class TestTypedFrozenDict(unittest.TestCase):

    def test_init_and_access(self):
        fd = TypedFrozenDict(str, int, {'a': '1'})
        self.assertEqual(fd['a'], 1)
        self.assertEqual(fd.data, dict({'a': 1}))

    def test_immutability(self):
        fd = TypedFrozenDict(str, int, {'x': 2})
        with self.assertRaises(TypeError):
            fd['x'] = 3
        with self.assertRaises(TypeError):
            fd.data['x'] = 3

    def test_repr(self):
        fd = TypedFrozenDict(str, int, {'z': 99})
        self.assertIn("TypedFrozenDict<str, int>", repr(fd))


if __name__ == '__main__':
    unittest.main()
