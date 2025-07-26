import unittest

from concrete_classes import MutableDict, ImmutableDict


class DictionaryTest(unittest.TestCase):

    def test_init_access_and_eq(self):
        dic = MutableDict[str, int]({'a': 1, 'b': '2'}, _coerce_values=True)
        # '2' is correctly coerced to 2
        self.assertEqual(dic.data, {'a': 1, 'b': 2})
        # Access to the keys returns the expected values
        self.assertEqual(dic['a'], 1)
        self.assertEqual(dic['b'], 2)
        self.assertNotEqual(dic['a'], '2')

        imd = ImmutableDict[str, int](dic)
        # Copying on another AbstractDict maintains the same access to keys and subjacent data
        self.assertEqual(dic.data, imd.data)
        self.assertEqual(dic['a'], imd['a'])
        # The original dict and its "copy" are still considered equal
        self.assertEqual(imd, dic)

        # Converting back to a MutableDict preserves equality
        mud = MutableDict[str, int](imd)
        self.assertEqual(dic, mud)

    def test_type_inference(self):
        dic = ImmutableDict.of({1: 'a', 2: 'b'})
        # Key type is inferred to int
        self.assertEqual(dic.key_type, int)
        # Value type is inferred to str
        self.assertEqual(dic.value_type, str)

        # Using of_keys_values creates an equal dict
        dic2 = ImmutableDict.of_keys_values([1, 2], ['a', 'b'])
        self.assertEqual(dic, dic2)

        dic3 = MutableDict.of_keys_values([1, '2'], ['a', 0])
        # Key type is inferred to int | str
        self.assertEqual(dic3.key_type, int | str)
        # Value type is inferred to int | str
        self.assertEqual(dic3.value_type, int | str)

    def test_immutability(self):
        fd = ImmutableDict[str, int]({'x': 2})
        with self.assertRaises(TypeError):
            fd['x'] = 3
        with self.assertRaises(TypeError):
            fd.data['x'] = 3

    def test_set_and_get(self):
        d = MutableDict[str, int]()
        with self.assertRaises(TypeError):
            d['x'] = '5'
        d['x'] = 5
        self.assertEqual(d['x'], 5)
        self.assertNotEqual(d['x'], '5')

    def test_keys_values_items(self):
        d = MutableDict[str, int]([('a', 1), ('b', 2)])
        self.assertEqual(set(d.keys()), {'a', 'b'})
        self.assertEqual(set(d.values()), {1, 2})
        self.assertIn(('a', 1), d.items())
        self.assertIn(('b', 2), d.items())
        self.assertEqual(list(zip(d.keys(), d.values())), list(d.items()))

    def test_repr(self):
        d = MutableDict[str, float]({'pi': 3.14})
        self.assertIn("MutableDict[str, float]", repr(d))

        fd = ImmutableDict[str, int]({'z': 99})
        self.assertIn("ImmutableDict[str, int]", repr(fd))

    def test_get(self):
        d = MutableDict[int, int]()
        self.assertEqual(d.get(0, 27), 27)

        d[0] = 1
        self.assertEqual(d.get(0, 27), 1)
        self.assertNotEqual(d.get(0, 27), 27)

    def test_clear(self):
        origin_data = {'pi': 3.14, 'e': 2.71}
        d = MutableDict[str, float](origin_data)
        str_float_empty = MutableDict[str, float]()
        str_str_empty = MutableDict[str, str]()
        d.clear()
        self.assertEqual(d, str_float_empty)
        self.assertNotEqual(d, str_str_empty)
        self.assertNotEqual(d.data, origin_data)

    def test_update(self):
        d = MutableDict[str, int]({'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5})
        d.update({'f': 6})
        self.assertEqual(d.data, {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6})
        d.update({'a': 0, 'g': 7})
        self.assertNotEqual(d['a'], 1)
        self.assertEqual(d.data, {'a': 0, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7})

    def test_map_values_and_filter(self):
        d = MutableDict[int, str]({0:'abc', 1:'def', 2:'xyz'})
        mapped = d.map_values(lambda s: '__'+s+'__')
        self.assertEqual(mapped[0], '__abc__')
        self.assertEqual(mapped, MutableDict[int, str]({0:'__abc__', 1:'__def__', 2:'__xyz__'}))

        mapped_to_int = d.map_values(len)
        self.assertEqual(mapped_to_int, MutableDict[int, int]({0:3, 1:3, 2:3}))

        filtered_items = d.filter_items(lambda k, v: k > 0 and (v.startswith('x') or v.startswith('a')))
        self.assertEqual(filtered_items.data, {2:'xyz'})

        filtered_keys = d.filter_keys(lambda k: k > 0)
        self.assertEqual(filtered_keys.data, {1:'def', 2:'xyz'})

        filtered_values = d.filter_values(lambda v: v.startswith('x') or v.startswith('a'))
        self.assertEqual(filtered_values.data, {0:'abc', 2:'xyz'})

    def test_subdict(self):
        d = ImmutableDict[str, int]({'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5})
        self.assertEqual(d['b': 'd'], ImmutableDict[str, int]({'b': 2, 'c': 3, 'd': 4}))
        self.assertEqual(d['d':], ImmutableDict[str, int]({'d': 4, 'e': 5}))
        self.assertEqual(d[:'c'], ImmutableDict[str, int]({'a': 1, 'b': 2, 'c': 3}))

        tpl_dic = ImmutableDict[tuple[int, str], float]({
            (1, 'a') : 0,
            (1, 'b') : 1.1,
            (1, 'z') : 2.25,
            (2, 'a') : 3.1415,
            (3, 'c') : 2.71
        })
        tpl_subdic = tpl_dic[(1, 'j') : (3, 'a')]
        self.assertEqual(tpl_subdic.data, {(1, 'z') : 2.25, (2, 'a') : 3.1415})


if __name__ == '__main__':
    unittest.main()
