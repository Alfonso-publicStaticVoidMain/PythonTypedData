import unittest

from abstract_classes import Collection, AbstractDict, AbstractSequence, AbstractSet, AbstractMutableDict, AbstractMutableSequence, AbstractMutableSet


class MyTestCase(unittest.TestCase):

    def test_forbidden_instantiation(self):
        with self.assertRaises(TypeError):
            c = Collection(str)
        with self.assertRaises(TypeError):
            d = AbstractDict(int, float)
        with self.assertRaises(TypeError):
            d = AbstractMutableDict(int, float)
        with self.assertRaises(TypeError):
            s = AbstractSequence(str)
        with self.assertRaises(TypeError):
            s = AbstractMutableSequence(str)
        with self.assertRaises(TypeError):
            s = AbstractSet(bool)
        with self.assertRaises(TypeError):
            s = AbstractMutableSet(bool)

if __name__ == '__main__':
    unittest.main()
