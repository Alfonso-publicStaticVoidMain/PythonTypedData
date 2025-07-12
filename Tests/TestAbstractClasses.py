import unittest

from Mixins import Collection, Dictionary, Sequence, Set


class MyTestCase(unittest.TestCase):

    def test_forbidden_instantiation(self):
        with self.assertRaises(TypeError):
            c = Collection(str)
        with self.assertRaises(TypeError):
            d = Dictionary(int, float)
        with self.assertRaises(TypeError):
            seq = Sequence(str)
        with self.assertRaises(TypeError):
            st = Set(bool)

if __name__ == '__main__':
    unittest.main()
