import unittest

from abstract_classes.collection import Collection
from abstract_classes.abstract_set import AbstractSet
from concrete_classes.list import MutableList, ImmutableList
from concrete_classes.set import MutableSet, ImmutableSet


class TestCollection(unittest.TestCase):

    def test_repr_and_bool(self):
        mul = MutableList[str]('a', 'b')
        self.assertTrue(mul)
        self.assertIn("MutableList[str]", repr(mul))

        iml = ImmutableList[str]('x')
        self.assertTrue(iml)
        self.assertIn("ImmutableList[str]", repr(iml))

        empty_lst = MutableList[int]()
        self.assertFalse(empty_lst)

        empty_imlist = ImmutableList[str]()
        self.assertFalse(empty_imlist)

        st = MutableSet[str]('a', 'b')
        self.assertTrue(st)
        self.assertIn('MutableSet[str]', repr(st))

        ims = ImmutableSet[frozenset[complex]](frozenset({2j, 1 + 1j}))
        self.assertTrue(ims)
        self.assertIn('ImmutableSet[frozenset[complex]]', repr(ims))

        s = MutableSet[str]()
        self.assertFalse(s)

        s.add('a')
        self.assertTrue(s)

    def test_contains(self):
        mus = MutableSet[int](0, 1, 2)
        self.assertTrue(0 in mus)
        self.assertTrue([0, 1] in mus)
        self.assertFalse([2, 3] in mus)

        mul = MutableList[str]('a', 'b', 'c', 2)
        self.assertTrue('a' in mul)
        self.assertTrue('2' in mul)
        self.assertFalse(2 in mul)
        self.assertTrue({'a', 'b', '2'} in mul)
        self.assertFalse({'d'} in mul)

    def test_copy(self):
        lst = MutableList[int](1, 2)
        new_lst = lst.copy()
        self.assertEqual(lst, new_lst)
        self.assertIsNot(lst, new_lst)

        nested_lst = MutableList[ImmutableList[int]](ImmutableList.of(0, 1), ImmutableList.of(0, 0))
        new_nested_lst = nested_lst.copy(deep=True)
        self.assertEqual(nested_lst, new_nested_lst)
        self.assertEqual(nested_lst[0], new_nested_lst[0])
        self.assertIsNot(nested_lst[0], new_nested_lst[0])
        self.assertEqual(nested_lst[1], new_nested_lst[1])
        self.assertIsNot(nested_lst[1], new_nested_lst[1])

    def test_map_filter_flatmap(self):
        lst = MutableList[int](1, 2, 3)
        self.assertEqual(lst.map(lambda x: x * 2), MutableList[int](2, 4, 6))
        self.assertEqual(lst.filter(lambda x: x % 2 == 1), MutableList[int](1, 3))
        self.assertEqual(lst.flatmap(lambda x: [x, x + 10]), MutableList[int](1, 11, 2, 12, 3, 13))

        iml = ImmutableList[int](1, 2, 3)
        self.assertEqual(iml.map(lambda x: x + 1), ImmutableList[int](2, 3, 4))
        self.assertEqual(iml.filter(lambda x: x % 2 == 1), ImmutableList[int]([1, 3]))
        self.assertEqual(iml.flatmap(lambda x: [x, -x]), ImmutableList[int](1, -1, 2, -2, 3, -3))

        mus = MutableSet[int](1, 2)
        self.assertEqual(mus.map(lambda x: x * 2), MutableSet[int](2, 4))
        self.assertEqual(mus.filter(lambda x: x > 1), MutableSet[int](2))
        self.assertEqual(mus.map(lambda x: x + 1).filter(lambda x: x % 2 == 0), MutableSet[int](2))
        self.assertEqual(mus.flatmap(lambda x: [x, -x]), MutableSet[int](1, -1, 2, -2))

        ims = ImmutableSet[int](1, 2)
        self.assertEqual(ims.map(lambda x: x * 2), ImmutableSet[int](2, 4))
        self.assertEqual(ims.filter(lambda x: x > 1), ImmutableSet[int](2))
        self.assertEqual(ims.map(lambda x: x + 1).filter(lambda x: x % 2 == 0), ImmutableSet[int](2))
        self.assertEqual(ims.flatmap(lambda x: [x, -x]), ImmutableSet[int](1, -1, 2, -2))

    def test_any_all_none_match(self):
        iml = ImmutableList[int](1, 2, 3, 4, 6, 12)
        self.assertTrue(iml.all_match(lambda n: 12 % n == 0))
        self.assertFalse(iml.any_match(lambda n: n < 0))
        self.assertTrue(iml.none_match(lambda n: n < 0))

    def test_reduce(self):
        mul = MutableList[int](0, 1, 2, 3)
        self.assertEqual(mul.reduce(lambda x, y: x + y), 6)

        self.assertEqual(ImmutableList[int]().reduce(lambda x, y: x + y, 0), 0)

        str_lst = ImmutableList[str]('J', 'A', 'V', 'A')
        self.assertEqual(str_lst.reduce(lambda s1, s2: s1 + s2, '_'), '_JAVA')

    def test_for_each(self):
        acc = []
        lst = MutableList[str]('a', 'b')
        lst.for_each(lambda x: acc.append(x.upper()))
        self.assertEqual(acc, ['A', 'B'])

    def test_max_min(self):
        lst = MutableList[int](1, 2, 5, 2)
        self.assertEqual(lst.max(), 5)
        self.assertIsNone(MutableList[int]().max())

        self.assertEqual(lst.min(), 1)
        self.assertIsNone(MutableList[int]().min())

        mus = MutableSet[float](-1, 0, 1.25)
        self.assertEqual(mus.max(), 1.25)
        self.assertEqual(mus.min(), -1)
        self.assertEqual(mus.min(), -1.0)

    def test_collect(self):
        mul = MutableList[int](1, 2, 3, 4, 5)
        dic = mul.collect(
            supplier=lambda:{},  # Initial supplier gives an empty dict to start
            accumulator=lambda d, n: d.__setitem__(n, 2**n),  # Accumulator adds the pair n : 2**n
            finisher=lambda d: d | {0: 1}  # Finisher adds the key 0: 1
        )
        self.assertEqual(dic, {0: 1, 1: 2, 2: 4, 3: 8, 4: 16, 5: 32})

    def test_stateful_collect(self):
        mul = MutableList[int](0, 0, 1, 1, 1, 2)
        # Using stateful_collect to simulate .distinct()
        def update(acc: MutableList[int], state: set, element: int):
            if element not in state:
                state.add(element)
                acc.append(element)

        dst_mul = mul.stateful_collect(
            supplier=lambda:MutableList[int](),
            state_supplier=set,
            accumulator=update,
            finisher=lambda acc, _ : ImmutableList[int](acc)
        )
        self.assertEqual(dst_mul, ImmutableList[int](0, 1, 2))

    def test_group_by_partition_by(self):
        class TestClass:
            def __init__(self, number: int, name: str):
                self.number = number
                self.name = name

        cosa_0 = TestClass(0, 'cosa 0')
        cosa_1 = TestClass(0, 'cosa 1')
        cosa_2 = TestClass(1, 'cosa 2')
        cosa_3 = TestClass(1, 'cosa 3')
        cosa_4 = TestClass(2, 'cosa 4')
        tml = MutableList[TestClass](cosa_0, cosa_1, cosa_2, cosa_3, cosa_4)

        grouped = tml.group_by(lambda test : test.number)
        self.assertEqual(grouped, {
            0 : MutableList[TestClass](cosa_0, cosa_1),
            1 : MutableList.of(cosa_2, cosa_3),
            2 : MutableList[TestClass](cosa_4)
        })

        partitioned = tml.partition_by(lambda test : test.number > 0)
        self.assertEqual(partitioned, {
            True : MutableList[TestClass](cosa_2, cosa_3, cosa_4),
            False : MutableList[TestClass](cosa_0, cosa_1)
        })

    def test_map_thoroughly(self):
        mul = MutableList[int](1, 2, 3)
        mapped_to_int = mul.map(lambda x : x+1)
        self.assertEqual(mapped_to_int, MutableList[int](2, 3, 4))

        mapped_to_int_coerced = mul.map(lambda x : str(x) * x, int, _coerce=True)
        self.assertEqual(mapped_to_int_coerced, MutableList[int](1, 22, 333))

        mapped_to_str = mul.map(lambda x : 'a' * x)
        self.assertEqual(mapped_to_str, MutableList[str]('a', 'aa', 'aaa'))

        mapped_to_str_coerced = mul.map(lambda x : 1j + x, str)
        self.assertEqual(mapped_to_str_coerced, MutableList[str]('(1+1j)', '(2+1j)', '(3+1j)'))

    def test_to_dict(self):
        mul = MutableList[int](0, 1, 2)
        dic = mul.to_dict(key_mapper=str)
        self.assertEqual(dic, {'0':0, '1':1, '2':2})

        iml = ImmutableList[str]('1_a', '2_b')
        dic = iml.to_dict(lambda s : int(s[0]), lambda s : s[-1])
        self.assertEqual(dic, {1:'a', 2:'b'})

    def test_abstract_classes(self):
        lst = MutableList[AbstractSet[int]]()
        lst.append(MutableSet[int](1, 2))
        lst.append(ImmutableSet[int](2, 3))
        self.assertEqual(lst, MutableList[AbstractSet[int]](MutableSet[int](1, 2), ImmutableSet[int](2, 3)))

        clt_lst = MutableList[Collection[str]]()
        a = MutableSet[str]('a')
        b = ImmutableSet[str]('b')
        c = MutableList[str]('c')
        d = ImmutableList[str]('d')
        clt_lst.append(a)
        clt_lst.append(b)
        clt_lst.append(c)
        clt_lst.append(d)
        self.assertEqual(clt_lst, MutableList[Collection[str]](a, b, c, d))


if __name__ == '__main__':
    unittest.main()
