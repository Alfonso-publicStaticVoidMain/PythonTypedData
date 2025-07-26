import unittest

from concrete_classes import MutableList, MutableSet
from maybe import Maybe


class TestMaybe(unittest.TestCase):

    def test_init(self):
        self.assertEqual(Maybe[int](2).get(), 2)
        self.assertEqual(Maybe[int](2), Maybe.of(2))
        with self.assertRaises(TypeError):
            mb = Maybe[int]('2', _coerce=False)

        self.assertEqual(Maybe[int]('2', _coerce=True).get(), 2)
        self.assertEqual(Maybe[str](2, _coerce=False).get(), '2')
        self.assertEqual(Maybe[str](3.14, _coerce=False).get(), '3.14')

    def test_get_present_empty(self):
        with self.assertRaises(ValueError):
            Maybe[int].empty().get()

        self.assertTrue(Maybe[str].empty().is_empty())
        self.assertTrue(Maybe.of(2).is_present())

    def test_or_else(self):
        self.assertEqual(Maybe[int].empty().or_else(3), 3)
        with self.assertRaises(TypeError):
            Maybe[int].empty().or_else('a')
        self.assertEqual(Maybe[str].empty().or_else_get(lambda:""), "")

    def test_map(self):
        mb1 = Maybe[int](1)
        mb2 = mb1.map(lambda x : x + 1)
        self.assertEqual(mb2, Maybe[int](2))

        with self.assertRaises(ValueError):
            Maybe[int].empty().map(lambda x : 2*x)

        mb3 = mb1.map(lambda x : f'{x}{x}', int, _coerce=True)
        self.assertEqual(mb3, Maybe[int](11))

        mb4 = mb1.map(lambda x : x + 1, str)
        self.assertEqual(mb4, Maybe[str]('2'))

        mb5 = Maybe[int].empty().map_or_else(lambda x : x + 1, 0)
        self.assertEqual(mb5, 0)

    def test_repr(self):
        mb = Maybe[list[int]]([0, 1, 2])
        self.assertIn('Maybe[list[int]]', repr(mb))

        mb2 = Maybe.of(MutableList[MutableSet[int]](MutableSet.of(0, 1), MutableSet.of(0, -1)))
        self.assertIn('Maybe[MutableList[MutableSet[int]]]', repr(mb2))

if __name__ == '__main__':
    unittest.main()
