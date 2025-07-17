import unittest

from concrete_classes import MutableDict, ImmutableDict


class DictionaryTest(unittest.TestCase):

    def test_init_access_and_eq(self):
        dic = MutableDict(str, int, {'a': 1, 'b': '2'}, _coerce_values=True)
        self.assertEqual(dic.data, {'a': 1, 'b': 2})
        self.assertEqual(dic['a'], 1)
        self.assertEqual(dic['b'], 2)

        imd = ImmutableDict(str, int, dic)
        self.assertEqual(dic.data, imd.data)
        self.assertEqual(dic['a'], imd['a'])
        self.assertNotEqual(imd, dic)

        mud = MutableDict(str, int, imd)
        self.assertEqual(dic, mud)

    def test_type_inference(self):
        dic = ImmutableDict.of({1: 'a', 2: 'b'})
        self.assertEqual(dic.key_type, int)
        self.assertEqual(dic.value_type, str)

    def test_immutability(self):
        fd = ImmutableDict(str, int, {'x': 2})
        with self.assertRaises(TypeError):
            fd['x'] = 3
        with self.assertRaises(TypeError):
            fd.data['x'] = 3

    def test_set_and_get(self):
        d = MutableDict(str, int)
        with self.assertRaises(TypeError):
            d['x'] = '5'
        d['x'] = 5
        self.assertEqual(d['x'], 5)
        self.assertNotEqual(d['x'], '5')

    def test_keys_values_items(self):
        d = MutableDict(str, int, [('a', 1), ('b', 2)])
        self.assertEqual(set(d.keys()), {'a', 'b'})
        self.assertEqual(set(d.values()), {1, 2})
        self.assertIn(('a', 1), d.items())
        self.assertIn(('b', 2), d.items())
        self.assertEqual(list(zip(d.keys(), d.values())), list(d.items()))

    def test_repr(self):
        d = MutableDict(str, float, {'pi': 3.14})
        self.assertIn("MutableDict<str, float>", repr(d))

        fd = ImmutableDict(str, int, {'z': 99})
        self.assertIn("ImmutableDict<str, int>", repr(fd))

    def test_get(self):
        d = MutableDict(int, int)
        self.assertEqual(d.get(0, 27), 27)

        d[0] = 1
        self.assertEqual(d.get(0, 27), 1)
        self.assertNotEqual(d.get(0, 27), 27)

    def test_clear(self):
        d = MutableDict(str, float, {'pi': 3.14, 'e': 2.71})
        str_float_empty = MutableDict(str, float)
        str_str_empty = MutableDict(str, str)
        d.clear()
        self.assertEqual(d, str_float_empty)
        self.assertNotEqual(d, str_str_empty)
        self.assertNotEqual(d.data, {'pi': 3.14, 'e': 2.71})

    def test_update(self):
        d = MutableDict(str, int, {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5})
        d.update({'f': 6})
        self.assertEqual(d.data, {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6})
        d.update({'a': 0, 'g': 7})
        self.assertNotEqual(d['a'], 1)
        self.assertEqual(d.data, {'a': 0, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7})

    def test_map_values_and_filter(self):
        d = MutableDict(int, str, {0:'abc', 1:'def', 2:'xyz'})
        mapped = d.map_values(lambda s: '__'+s+'__', str)
        self.assertEqual(mapped[0], '__abc__')

        filtered_items = d.filter_items(lambda k, v: k > 0 and (v.startswith('x') or v.startswith('a')))
        self.assertEqual(filtered_items.data, {2:'xyz'})

        filtered_keys = d.filter_keys(lambda k: k > 0)
        self.assertEqual(filtered_keys.data, {1:'def', 2:'xyz'})

        filtered_values = d.filter_values(lambda v: v.startswith('x') or v.startswith('a'))
        self.assertEqual(filtered_values.data, {0:'abc', 2:'xyz'})

    def test_subdict(self):
        d = ImmutableDict(str, int, {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5})
        sd = d.subdict('b', 'd')
        self.assertEqual(sd, ImmutableDict(str, int, {'b': 2, 'c': 3, 'd': 4}))


if __name__ == '__main__':
    unittest.main()
