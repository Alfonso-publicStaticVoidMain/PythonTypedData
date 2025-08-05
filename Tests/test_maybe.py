import unittest
from typing import Callable, Any

from concrete_classes.list import MutableList
from concrete_classes.set import MutableSet
from concrete_classes.maybe import Maybe


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

        mb2 = Maybe.of(MutableList[MutableSet[int]](MutableSet.of_values(0, 1), MutableSet.of_values(0, -1)))
        self.assertIn('Maybe[MutableList[MutableSet[int]]]', repr(mb2))

    def test_getattr(self):
        class Dummy:
            def __init__(self, num: int):
                self.num = num

            def get_double(self):
                return self.num * 2

        mb = Maybe.of(Dummy(2))
        self.assertEqual(mb.get_double(), 4)
        with self.assertRaises(TypeError):
            len(mb)
        with self.assertRaises(TypeError):
            mb(1)
        with self.assertRaises(TypeError):
            2 in mb
        with self.assertRaises(TypeError):
            for x in mb: pass
        with self.assertRaises(TypeError):
            len(mb)

        mb = Maybe.of([0, 1, 2])
        mb.append(3)
        self.assertEqual(mb, Maybe.of([0, 1, 2, 3]))
        self.assertEqual(mb[0], 0)
        self.assertTrue(3 in mb)
        self.assertEqual(len(mb), 4)
        with self.assertRaises(IndexError):
            mb[4]

        mb = Maybe[str].empty()
        with self.assertRaises(AttributeError):
            mb.startswith('_')
        with self.assertRaises(ValueError):
            len(mb)
        with self.assertRaises(ValueError):
            mb(1)
        with self.assertRaises(ValueError):
            for x in mb: pass

        mb = Maybe.of(lambda x : x + 1)
        self.assertEqual(mb(1), 2)

if __name__ == '__main__':
    unittest.main()
