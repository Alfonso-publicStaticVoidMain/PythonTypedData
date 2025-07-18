import unittest

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
            Maybe.empty(int).get()

        self.assertTrue(Maybe.empty(str).is_empty())
        self.assertTrue(Maybe.of(2).is_present())


    def test_or_else(self):
        self.assertEqual(Maybe.empty(int).or_else(3), 3)
        with self.assertRaises(TypeError):
            Maybe.empty(int).or_else('a')
        self.assertEqual(Maybe.empty(str).or_else_get(lambda:""), "")


if __name__ == '__main__':
    unittest.main()
