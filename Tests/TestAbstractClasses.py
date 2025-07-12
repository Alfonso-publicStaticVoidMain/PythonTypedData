import unittest

from Mixins import Collection, AbstractDict, AbstractSequence, AbstractSet


class MyTestCase(unittest.TestCase):

    def test_forbidden_instantiation(self):
        with self.assertRaises(TypeError):
            c = Collection(str)
        with self.assertRaises(TypeError):
            d = AbstractDict(int, float)
        with self.assertRaises(TypeError):
            seq = AbstractSequence(str)
        with self.assertRaises(TypeError):
            st = AbstractSet(bool)

if __name__ == '__main__':
    unittest.main()
