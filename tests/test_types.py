"""Tests for _types.py — type_info_from_param_type and _type_info_from_callable."""

from __future__ import annotations

import click
import pytest

from clickdump._types import _type_info_from_callable, type_info_from_param_type
from clickdump.models import FileTypeInfo, TypeInfo


class TestBuiltinTypes:
    @pytest.mark.parametrize(
        "param_type, expected",
        [
            (click.STRING, ("str", "builtins", True)),
            (click.INT, ("int", "builtins", True)),
            (click.FLOAT, ("float", "builtins", True)),
            (click.BOOL, ("bool", "builtins", True)),
            (click.UNPROCESSED, ("str", "builtins", True)),
        ],
    )
    def test_builtin(self, param_type, expected):
        type_info, file_type_info, choices = type_info_from_param_type(param_type)
        assert type_info.name == expected[0]
        assert type_info.module == expected[1]
        assert type_info.builtin == expected[2]
        assert file_type_info is None
        assert choices is None


class TestStandardTypes:
    def test_uuid(self):
        type_info, _, _ = type_info_from_param_type(click.UUID)
        assert type_info == TypeInfo(name="UUID", module="uuid")

    def test_datetime(self):
        type_info, _, _ = type_info_from_param_type(click.DateTime())
        assert type_info == TypeInfo(name="datetime", module="datetime")

    def test_int_range(self):
        type_info, _, _ = type_info_from_param_type(click.IntRange(0, 100))
        assert type_info == TypeInfo(name="int_range", module="click.types")

    def test_float_range(self):
        type_info, _, _ = type_info_from_param_type(click.FloatRange(0.0, 1.0))
        assert type_info == TypeInfo(name="float_range", module="click.types")

    def test_path(self):
        type_info, _, _ = type_info_from_param_type(click.Path())
        assert type_info == TypeInfo(name="Path", module="pathlib")


class TestChoice:
    def test_choice(self):
        type_info, _, choices = type_info_from_param_type(
            click.Choice(["red", "green", "blue"])
        )
        assert type_info == TypeInfo(name="choice", module="click.types")
        assert choices == ["red", "green", "blue"]


class TestFile:
    def test_file_defaults(self):
        type_info, file_type_info, _ = type_info_from_param_type(click.File())
        assert type_info == TypeInfo(name="FileType", module="click.types")
        assert isinstance(file_type_info, FileTypeInfo)
        assert file_type_info.mode == "r"

    def test_file_custom(self):
        type_info, file_type_info, _ = type_info_from_param_type(
            click.File(mode="rb", encoding="utf-8")
        )
        assert file_type_info.mode == "rb"
        assert file_type_info.encoding == "utf-8"


class TestTuple:
    def test_single_type(self):
        type_info, _, _ = type_info_from_param_type(click.Tuple([str]))
        assert type_info.name == "text"
        assert type_info.module == "click.types"

    def test_multiple_types(self):
        type_info, _, _ = type_info_from_param_type(click.Tuple([str, int]))
        assert type_info.name == "text_integer"
        assert type_info.module == "click.types"


class TestFallback:
    def test_unknown_type(self):
        type_info, file_type_info, choices = type_info_from_param_type(object())
        assert type_info == TypeInfo(name="unknown", serializable=False)
        assert file_type_info is None
        assert choices is None


class TestFuncParamType:
    def test_func_with_callable(self):
        type_info, _, _ = type_info_from_param_type(click.types.FuncParamType(func=int))
        assert type_info == TypeInfo(name="int", builtin=True)


class TestCallableInfo:
    def test_none(self):
        assert _type_info_from_callable(None) == TypeInfo(
            name="str", module="builtins", builtin=True
        )

    @pytest.mark.parametrize(
        "func, expected",
        [
            (int, ("int", True)),
            (float, ("float", True)),
            (str, ("str", True)),
            (bool, ("bool", True)),
            (complex, ("complex", True)),
            (bytes, ("bytes", True)),
            (bytearray, ("bytearray", True)),
        ],
    )
    def test_builtin_types(self, func, expected):
        result = _type_info_from_callable(func)
        assert result.name == expected[0]
        assert result.builtin == expected[1]

    def test_lambda(self):
        result = _type_info_from_callable(lambda x: x)
        assert result.name == "<lambda>"
        assert result.serializable is False

    def test_named_function(self):
        def my_converter(s):
            return s

        result = _type_info_from_callable(my_converter)
        assert result.name == "my_converter"
        assert result.module == "test_types"
        assert result.serializable is True

    def test_repr_fallback(self):
        class NoName:
            __repr__ = lambda self: "<NoName>"

        result = _type_info_from_callable(NoName())
        assert result.serializable is False
