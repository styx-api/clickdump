"""Tests for _values.py — serialize_value and its helpers."""

from __future__ import annotations

import base64
from enum import Enum

import pytest

from clickdump._values import serialize_value


class Color(Enum):
    RED = "red"
    GREEN = [1, 2]


class TestPrimitives:
    @pytest.mark.parametrize("value", [None, True, False, 42, 3.14, "hello"])
    def test_passthrough(self, value):
        assert serialize_value(value) is value


class TestSequence:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ([1, "two", 3.0], [1, "two", 3.0]),
            ((1, 2, 3), [1, 2, 3]),
            ([[1], [2, 3]], [[1], [2, 3]]),
            ([], []),
        ],
    )
    def test_sequence(self, value, expected):
        assert serialize_value(value) == expected


class TestDict:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ({"a": 1}, {"a": 1}),
            ({"x": {"y": 1}}, {"x": {"y": 1}}),
            ({}, {}),
        ],
    )
    def test_dict(self, value, expected):
        assert serialize_value(value) == expected

    def test_non_string_keys(self):
        result = serialize_value({1: "a", (2, 3): "b"})
        assert result == {"1": "a", "(2, 3)": "b"}


class TestSet:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ({3, 1, 2}, [1, 2, 3]),
            ({"b", "a", "c"}, ["a", "b", "c"]),
            (set(), []),
        ],
    )
    def test_set(self, value, expected):
        assert serialize_value(value) == {"__set__": expected}


class TestFrozenSet:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (frozenset({30, 10, 20}), [10, 20, 30]),
            (frozenset({"z", "a", "m"}), ["a", "m", "z"]),
        ],
    )
    def test_frozenset(self, value, expected):
        assert serialize_value(value) == {"__frozenset__": expected}


class TestRange:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (range(1, 10, 2), [1, 10, 2]),
            (range(5), [0, 5, 1]),
        ],
    )
    def test_range(self, value, expected):
        assert serialize_value(value) == {"__range__": expected}


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
    @pytest.mark.parametrize(
        "value, expected",
        [
            (b"hello", {"__bytes__": "hello"}),
            (
                b"\xff\xfe",
                {"__bytes_b64__": base64.b64encode(b"\xff\xfe").decode("ascii")},
            ),
        ],
    )
    def test_bytes(self, value, expected):
        assert serialize_value(value) == expected


class TestType:
    def test_type(self):
        assert serialize_value(int) == {
            "__type__": True,
            "name": "int",
            "module": "builtins",
        }


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
        assert serialize_value(a)[0] == {"__circular_ref__": True}

    def test_circular_dict(self):
        a = {}
        a["self"] = a
        assert serialize_value(a)["self"] == {"__circular_ref__": True}
