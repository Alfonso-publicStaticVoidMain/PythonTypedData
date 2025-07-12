import unittest

from DataContainers import MutableDict


class TestTypedDict(unittest.TestCase):

    def test_init_and_access(self):
        d = MutableDict(str, int, {'a': 1, 'b': '2'})
        self.assertEqual(d.data, {'a': 1, 'b': 2})
        self.assertEqual(d['a'], 1)

    def test_set_and_get(self):
        d = MutableDict(str, int)
        d['x'] = '5'
        self.assertEqual(d['x'], 5)

    def test_keys_values_items(self):
        d = MutableDict(str, int, [('a', 1), ('b', 2)])
        self.assertEqual(set(d.keys()), {'a', 'b'})
        self.assertEqual(set(d.values()), {1, 2})
        self.assertIn(('a', 1), d.items())

    def test_repr(self):
        d = MutableDict(str, float, {'pi': 3.14})
        self.assertIn("MutableDict<str, float>", repr(d))


if __name__ == '__main__':
    unittest.main()
