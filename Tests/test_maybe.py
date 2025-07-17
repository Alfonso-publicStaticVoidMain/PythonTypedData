import unittest

from maybe import Maybe


class TestMaybe(unittest.TestCase):
    def test_init(self):
        self.assertEqual(Maybe(2, int).get(), 2)
        self.assertEqual(Maybe(2), Maybe.of(2))
        with self.assertRaises(TypeError):
            mb = Maybe('2', int, _coerce=False)

        self.assertEqual(Maybe('2', int, _coerce=True).get(), 2)
        self.assertEqual(Maybe(2, str, _coerce=False).get(), '2')
        self.assertEqual(Maybe(3.14, str, _coerce=False).get(), '3.14')

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
