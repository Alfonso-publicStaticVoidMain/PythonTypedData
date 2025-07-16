import unittest

from concrete_classes import MutableList
from type_validation import _infer_type


class Dummy:
    pass

class TestTypeInference(unittest.TestCase):

    def test_list_of_ints(self):
        self.assertEqual(_infer_type([1, 2, 3]), list[int])

    def test_set_of_floats(self):
        self.assertEqual(_infer_type({1.0, 2.5}), set[float])

    def test_frozenset_of_str(self):
        self.assertEqual(_infer_type(frozenset(['a', 'b'])), frozenset[str])

    def test_mixed_list(self):
        self.assertEqual(_infer_type([1, "a"]), list[int | str])

    def test_dict_str_int(self):
        self.assertEqual(_infer_type({"a": 1, "b": 2}), dict[str, int])

    def test_dict_mixed_values(self):
        self.assertEqual(_infer_type({"a": 1, "b": "x"}), dict[str, int | str])

    def test_tuple_fixed_types(self):
        self.assertEqual(_infer_type((1, "a", 3.0)), tuple[int, str, float])

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            _infer_type([])

    def test_empty_dict_raises(self):
        with self.assertRaises(ValueError):
            _infer_type({})

    def test_nested_list(self):
        self.assertEqual(_infer_type([[1, 2], [3, 4]]), list[list[int]])

    def test_deeply_nested_structure(self):
        value = [[{"a": 1}], [{"b": 2}]]
        expected = list[list[dict[str, int]]]
        self.assertEqual(_infer_type(value), expected)

    def test_tuple_with_same_types(self):
        self.assertEqual(_infer_type((1, 2)), tuple[int, int])

    def test_custom_object_type(self):
        obj = Dummy()
        self.assertEqual(_infer_type(obj), Dummy)

    def test_mutable_list(self):
        self.assertEqual(_infer_type(MutableList([1, 1, 1], int)), MutableList[int])

        lst = [MutableList([0, 1], int), MutableList([2, 3], int), MutableList([], int)]
        self.assertEqual(_infer_type(lst), list[MutableList[int]])


if __name__ == '__main__':
    unittest.main()
