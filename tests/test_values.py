"""Tests for _values.py — serialize_value and its helpers."""

from __future__ import annotations

import base64
from enum import Enum

from clickdump._values import serialize_value


class Color(Enum):
    RED = "red"
    GREEN = [1, 2]


class TestPrimitives:
    def test_none(self):
        assert serialize_value(None) is None

    def test_bool_passthrough(self):
        assert serialize_value(True) is True
        assert serialize_value(False) is False

    def test_int_passthrough(self):
        assert serialize_value(42) == 42

    def test_float_passthrough(self):
        assert serialize_value(3.14) == 3.14

    def test_str_passthrough(self):
        assert serialize_value("hello") == "hello"


class TestSequence:
    def test_list(self):
        assert serialize_value([1, "two", 3.0]) == [1, "two", 3.0]

    def test_tuple(self):
        assert serialize_value((1, 2, 3)) == [1, 2, 3]

    def test_nested_sequence(self):
        assert serialize_value([[1], [2, 3]]) == [[1], [2, 3]]

    def test_empty_list(self):
        assert serialize_value([]) == []


class TestDict:
    def test_dict(self):
        assert serialize_value({"a": 1, "b": "two"}) == {"a": 1, "b": "two"}

    def test_dict_non_string_keys(self):
        result = serialize_value({1: "a", (2, 3): "b"})
        assert result == {"1": "a", "(2, 3)": "b"}

    def test_nested_dict(self):
        assert serialize_value({"x": {"y": 1}}) == {"x": {"y": 1}}

    def test_empty_dict(self):
        assert serialize_value({}) == {}


class TestSet:
    def test_set(self):
        result = serialize_value({3, 1, 2})
        assert result == {"__set__": [1, 2, 3]}

    def test_set_sorted(self):
        result = serialize_value({"b", "a", "c"})
        assert result == {"__set__": ["a", "b", "c"]}

    def test_empty_set(self):
        assert serialize_value(set()) == {"__set__": []}


class TestFrozenSet:
    def test_frozenset(self):
        result = serialize_value(frozenset({30, 10, 20}))
        assert result == {"__frozenset__": [10, 20, 30]}

    def test_frozenset_sorted(self):
        result = serialize_value(frozenset({"z", "a", "m"}))
        assert result == {"__frozenset__": ["a", "m", "z"]}


class TestEnum:
    def test_enum(self):
        result = serialize_value(Color.RED)
        assert result == {
            "__enum__": True,
            "class": "Color",
            "module": "test_values",
            "value": "red",
            "name": "RED",
        }

    def test_enum_nested_value(self):
        result = serialize_value(Color.GREEN)
        assert result["__enum__"] is True
        assert result["value"] == [1, 2]


class TestBytes:
    def test_bytes_utf8(self):
        result = serialize_value(b"hello")
        assert result == {"__bytes__": "hello"}

    def test_bytes_non_utf8(self):
        raw = b"\xff\xfe"
        result = serialize_value(raw)
        expected_b64 = base64.b64encode(raw).decode("ascii")
        assert result == {"__bytes_b64__": expected_b64}


class TestRange:
    def test_range(self):
        assert serialize_value(range(1, 10, 2)) == {"__range__": [1, 10, 2]}

    def test_range_defaults(self):
        assert serialize_value(range(5)) == {"__range__": [0, 5, 1]}


class TestType:
    def test_type(self):
        result = serialize_value(int)
        assert result == {"__type__": True, "name": "int", "module": "builtins"}


class TestNonSerializable:
    def test_non_serializable(self):
        obj = object()
        result = serialize_value(obj)
        assert result["__serializable__"] is False
        assert result["__type_name__"] == "object"
        assert "__repr__" in result


class TestCircularRef:
    def test_circular_list(self):
        a = []
        a.append(a)
        result = serialize_value(a)
        assert result[0] == {"__circular_ref__": True}

    def test_circular_dict(self):
        a = {}
        a["self"] = a
        result = serialize_value(a)
        assert result["self"] == {"__circular_ref__": True}
