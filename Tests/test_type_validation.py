import unittest
from typing import Literal, Union, TYPE_CHECKING

from abstract_classes import AbstractSet

if TYPE_CHECKING:
    from concrete_classes import MutableDict, MutableSet, ImmutableDict, ImmutableSet, MutableList, ImmutableList
    from maybe import Maybe
from type_validation import _validate_type


class TestTypeValidation(unittest.TestCase):

    def test_validate_numeric_subtypes(self):
        self.assertTrue(_validate_type(1, int))
        self.assertFalse(_validate_type(1, float))
        self.assertFalse(_validate_type(1.5, int))
        self.assertTrue(_validate_type(1.5, float))

    def test_validate_tuple(self):
        tpl = (1, 2, 3)
        self.assertTrue(_validate_type(tpl, tuple[int, int, int]))
        self.assertTrue(_validate_type(tpl, tuple[int, ...]))
        self.assertTrue(_validate_type((1, 0.1, 1), tuple[int, float, int]))
        self.assertFalse(_validate_type((1, 'a', 3), tuple[int, ...]))
        self.assertFalse(_validate_type((1, 2.0), tuple[int, float, int]))
        self.assertFalse(_validate_type((1, 2, 3, 4), tuple[int, float, int]))

    def test_validate_list(self):
        lst = [0, 1, 2, 3]
        self.assertTrue(_validate_type(lst, list[int]))
        self.assertFalse(_validate_type(lst, list[float]))
        self.assertFalse(_validate_type(lst, tuple[int, ...]))

    def test_validate_sets(self):
        self.assertTrue(_validate_type({1, 2, 3}, set[int]))
        self.assertTrue(_validate_type(frozenset({1.0, 2}), frozenset[int | float]))
        self.assertFalse(_validate_type({'a', 2}, set[int]))  # str is invalid

    def test_validate_dict(self):
        d = {1: "a", 2: "b"}
        self.assertTrue(_validate_type(d, dict[int, str]))
        self.assertFalse(_validate_type(d, dict[str, str]))
        self.assertFalse(_validate_type(d, dict[int, int]))

    def test_validate_nested_structures(self):
        nested_list = [[0, 1], [1, 2], [2, 3]]
        self.assertTrue(_validate_type(nested_list, list[list[int]]))
        self.assertFalse(_validate_type(nested_list, list[int]))

        lst_tpls = [(1, 'a'), (2, 'b')]
        self.assertTrue(_validate_type(lst_tpls, list[tuple[int, str]]))
        self.assertFalse(_validate_type(lst_tpls, tuple[int, str]))

        dic = {frozenset({0, 1}) : ['0', '1'], frozenset({-1, -2}) : ['-1', '-2']}
        self.assertTrue(_validate_type(dic, dict[frozenset[int], list[str]]))
        self.assertTrue(_validate_type(dic, dict[frozenset[int | float], list[str | bool]]))

    def test_validate_union_pipe(self):
        self.assertTrue(_validate_type({'a': '1', 'b': 1}, dict[str, int | str]))
        self.assertTrue(_validate_type((1, 'a'), tuple[int | str, int | str]))
        self.assertTrue(_validate_type((1, 'a'), tuple[int | str, ...]))
        self.assertFalse(_validate_type((1, 2), tuple[int | str, str]))

        self.assertEqual(_validate_type(1, int | float), _validate_type(1, Union[int, float]))

    def test_validate_deeply_nested(self):
        self.assertTrue(_validate_type([[[(1, 'a')]]], list[list[list[tuple[int, str]]]]))
        self.assertFalse(_validate_type([[[(1, 2)]]], list[list[list[tuple[int, str]]]]))
        self.assertTrue(_validate_type([[[[1], [2]], [[3], [4]]]], list[list[list[list[int]]]]))
        self.assertFalse(_validate_type([[[[1], ['2']]]], list[list[list[list[int]]]]))
        self.assertTrue(_validate_type([{"a": [1, 2], "b": [3]}, {"a": [4], "b": [5, 6]}], list[dict[str, list[int]]]))
        self.assertFalse(_validate_type([{"a": [1, "2"]}], list[dict[str, list[int]]]))
        self.assertTrue(_validate_type({
            (1, 'a'): [[1, 2]],
            (2, 'b'): [[3, 4]]
        }, dict[tuple[int, str], list[list[int]]]))
        self.assertFalse(_validate_type({
            (1, 'a'): [[1, "2"]]
        }, dict[tuple[int, str], list[list[int]]]))
        self.assertTrue(_validate_type(([{1, 2}, {3}], [[4, 5], [6]]), tuple[list[set[int]], list[list[int]]]))
        self.assertFalse(_validate_type(([{1, 'x'}], [[1]]), tuple[list[set[int]], list[list[int]]]))
        self.assertTrue(_validate_type({
            "layer1": [
                {"coords": [(1, 2.0), (3, 4.5)], "labels": ["a", "b"]},
                {"coords": [(5, 6.7)], "labels": ["c"]}
            ]
        }, dict[
            str,
            list[dict[
                str,
                list[tuple[int, float]] | list[str]
            ]]
        ]))
        self.assertFalse(_validate_type({
            "layer1": [
                {"coords": [(1, "oops")], "labels": ["a"]}
            ]
        }, dict[
            str,
            list[dict[
                str,
                list[tuple[int, float]] | list[str]
            ]]
        ]))

    def test_validate_literal(self):
        self.assertTrue(_validate_type('red', Literal['red', 'blue']))
        self.assertFalse(_validate_type('green', Literal['red', 'blue']))

    def test_validate_custom_classes(self):
        from concrete_classes import MutableDict, MutableSet, ImmutableDict, ImmutableSet, MutableList, ImmutableList
        from maybe import Maybe

        # --- Direct matches
        ml = MutableList[int]([1, 2, 3])
        self.assertTrue(_validate_type(ml, MutableList[int]))

        iml = ImmutableList[str]("a", "b")
        self.assertTrue(_validate_type(iml, ImmutableList[str]))

        md = MutableDict[str, int]({"a": 1, "b": 2})
        self.assertTrue(_validate_type(md, MutableDict[str, int]))

        id_ = ImmutableDict[int, float]({1: 1.0, 2: 2.0})
        self.assertTrue(_validate_type(id_, ImmutableDict[int, float]))

        ms = MutableSet[bool]({True, False})
        self.assertTrue(_validate_type(ms, MutableSet[bool]))

        ims = ImmutableSet[float](1.1, 2.2)
        self.assertTrue(_validate_type(ims, ImmutableSet[float]))

        mb = Maybe[int](42)
        self.assertTrue(_validate_type(mb, Maybe[int]))

        # --- Type mismatch
        self.assertFalse(_validate_type(MutableList[str]("a", "b"), MutableList[int]))
        self.assertFalse(_validate_type(MutableDict[str, str]({"a": "b"}), MutableDict[str, int]))
        self.assertFalse(_validate_type(MutableSet[float](1.0), MutableSet[str]))

        # --- Custom class nested in standard containers
        lst_of_custom = [MutableList[int]([1, 2]), MutableList[int](3, 4)]
        self.assertTrue(_validate_type(lst_of_custom, list[MutableList[int]]))

        dict_of_custom = {
            "x": MutableSet[int]({1, 2}),
            "y": MutableSet[int]({3, 4})
        }
        self.assertTrue(_validate_type(dict_of_custom, dict[str, MutableSet[int]]))

        # --- Nested custom within custom
        nested_custom = MutableList[MutableList[int]]([
            MutableList[int]([1]),
            MutableList[int]([2, 3])
        ])
        self.assertTrue(_validate_type(nested_custom, MutableList[MutableList[int]]))

        deeply_nested = MutableList[MutableDict[str, int]]([
            MutableDict[str, int]({"a": 1}),
            MutableDict[str, int]({"b": 2})
        ])
        self.assertTrue(_validate_type(deeply_nested, MutableList[MutableDict[str, int]]))

        # --- Union (|) with custom types
        union_test = [
            MutableSet[int]({1, 2}),
            ImmutableSet[int]({3, 4}),
        ]
        self.assertTrue(_validate_type(union_test, list[MutableSet[int] | ImmutableSet[int]]))
        self.assertTrue(_validate_type(union_test, list[AbstractSet[int]]))

        union_dict_test = MutableDict[str, str]({"a": "1"})
        self.assertTrue(_validate_type(union_dict_test, MutableDict[str, str] | ImmutableDict[str, str]))

        # --- Maybe as obj inside another structure
        optional_test = {
            "a": Maybe[int](1),
            "b": Maybe[int](2),
        }
        self.assertTrue(_validate_type(optional_test, dict[str, Maybe[int]]))

    def test_validate_against_abstract_classes(self):
        from concrete_classes import (
            AbstractSequence, AbstractSet, AbstractMutableSet, AbstractMutableSequence,
            AbstractDict, AbstractMutableDict, MutableList, MutableSet, MutableDict,
            ImmutableList, ImmutableSet, ImmutableDict
        )

        self.assertTrue(_validate_type(MutableList[int]([1, 2]), AbstractSequence[int]))
        self.assertTrue(_validate_type(ImmutableList[int](1, 2), AbstractSequence[int]))

        self.assertTrue(_validate_type(MutableSet[str]({"a"}), AbstractSet[str]))
        self.assertTrue(_validate_type(ImmutableSet[str].of("a", "b"), AbstractSet[str]))

        self.assertTrue(_validate_type(MutableSet[str]({"a"}), AbstractMutableSet[str]))
        self.assertFalse(_validate_type(ImmutableSet[str].of("a", "b"), AbstractMutableSet[str]))

        self.assertTrue(_validate_type(MutableDict[int, float]({1: 1.0}), AbstractDict[int, float]))
        self.assertTrue(_validate_type(ImmutableDict[int, float]({2: 3.0}), AbstractDict[int, float]))

        self.assertTrue(_validate_type(MutableDict[str, int]({"a": 1}), AbstractMutableDict[str, int]))
        self.assertFalse(_validate_type(ImmutableDict[str, int]({"a": 1}), AbstractMutableDict[str, int]))

    def test_validate_list_of_abstract(self):
        from concrete_classes import AbstractSet, MutableSet, ImmutableSet

        sets = [
            MutableSet[int]({1, 2}),
            ImmutableSet[int].of(3, 4),
            MutableSet[int]({5})
        ]
        self.assertTrue(_validate_type(sets, list[AbstractSet[int]]))
        self.assertFalse(_validate_type(sets, list[AbstractSet[str]]))

    def test_validate_nested_with_maybe_and_abstracts(self):
        from concrete_classes import MutableList, AbstractDict, MutableDict
        from maybe import Maybe

        nested = MutableList[Maybe[MutableDict[str, int]]]([
            Maybe[MutableDict[str, int]](MutableDict[str, int]({"a": 1})),
            Maybe[MutableDict[str, int]](MutableDict[str, int]({"b": 2}))
        ])
        self.assertFalse(_validate_type(nested, MutableList[Maybe[AbstractDict[str, int]]]))

    def test_invalid_generic_mismatch_deep(self):
        from concrete_classes import MutableList, MutableDict

        bad = MutableList[MutableDict[float, int]]([
            MutableDict[float, int]({1.1: 1}),
            MutableDict[float, int]({2.2: 2})
        ])
        self.assertFalse(_validate_type(bad, MutableList[MutableDict[str, int]]))

    def test_union_of_nested_customs_and_maybe(self):
        from concrete_classes import MutableSet, ImmutableSet
        from maybe import Maybe

        hybrid = [
            Maybe[MutableSet[int]](MutableSet[int]({1, 2})),
            Maybe[ImmutableSet[int]](ImmutableSet[int].of(3, 4)),
            Maybe[None](None)
        ]
        self.assertTrue(_validate_type(hybrid, list[Maybe[MutableSet[int]] | Maybe[ImmutableSet[int]] | Maybe[None]]))

    def test_collection_of_collections_of_custom_type(self):
        from concrete_classes import MutableSet, AbstractSet

        nested_sets = [
            [MutableSet[int]({1}), MutableSet[int]({2})],
            [MutableSet[int]({3})]
        ]
        self.assertTrue(_validate_type(nested_sets, list[list[AbstractSet[int]]]))

    def test_deeply_nested_mixed_mutable_immutable(self):
        from concrete_classes import MutableDict, ImmutableDict, AbstractDict

        obj = [
            {
                "first": MutableDict[int, str]({1: "one"}),
                "second": ImmutableDict[int, str]({2: "two"})
            },
            {
                "first": MutableDict[int, str]({3: "three"}),
                "second": ImmutableDict[int, str]({4: "four"})
            }
        ]
        self.assertTrue(_validate_type(obj, list[dict[str, AbstractDict[int, str]]]))

    def test_validate_maybe_inside_structure(self):
        from maybe import Maybe
        from concrete_classes import MutableList, MutableDict

        valid_dict = {
            "a": Maybe[int](1),
            "b": Maybe[int]()
        }
        self.assertTrue(_validate_type(valid_dict, dict[str, Maybe[int]]))

        nested = MutableList[Maybe[MutableDict[str, int]]]([
            Maybe.of(MutableDict[str, int]({"x": 1})),
            Maybe.empty(MutableDict[str, int])  # None present
        ])
        self.assertTrue(_validate_type(nested, MutableList[Maybe[MutableDict[str, int]]]))

    def test_validate_invalid_maybe_structures(self):
        from maybe import Maybe
        from concrete_classes import MutableDict

        self.assertFalse(_validate_type(Maybe[str]("hello"), Maybe[int]))
        self.assertFalse(_validate_type(Maybe[int](1), int))  # missing Maybe wrapper

        invalid_dict = MutableDict.of({
            "x": Maybe[int](),
            "y": "Maybe not"
        })
        self.assertFalse(_validate_type(invalid_dict, dict[str, Maybe[int]]))

    def test_validate_maybe_with_nested_unions(self):
        from maybe import Maybe
        from concrete_classes import MutableSet, ImmutableSet

        data = [
            Maybe.of(MutableSet[int]({1})),
            Maybe.of(ImmutableSet.of(2)),
            Maybe.empty(MutableSet[int])
        ]
        self.assertTrue(_validate_type(data, list[Maybe[MutableSet[int]] | Maybe[ImmutableSet[int]]]))
        self.assertFalse(_validate_type(data, list[Maybe[AbstractSet[int]]]))


if __name__ == '__main__':
    unittest.main()
