import unittest

from abstract_classes import Collection, AbstractDict, AbstractSequence, AbstractSet, AbstractMutableDict, AbstractMutableSequence, AbstractMutableSet


class TestAbstractClasses(unittest.TestCase):

    def test_forbidden_instantiation(self):
        with self.assertRaises(TypeError):
            col = Collection[int]()
        with self.assertRaises(TypeError):
            dic = AbstractDict[int, float]()
        with self.assertRaises(TypeError):
            aml = AbstractMutableDict[int, float]()
        with self.assertRaises(TypeError):
            seq = AbstractSequence[str]()
        with self.assertRaises(TypeError):
            amseq = AbstractMutableSequence[str]()
        with self.assertRaises(TypeError):
            ast = AbstractSet[bool]()
        with self.assertRaises(TypeError):
            amset = AbstractMutableSet[bool]()

if __name__ == '__main__':
    unittest.main()
