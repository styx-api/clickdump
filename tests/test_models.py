"""Tests for models.py — ActionType, ActionInfo, ParserInfo, and dataclasses."""

from __future__ import annotations

import pytest

from clickdump.models import (
    ActionInfo,
    ActionType,
    ArgumentGroup,
    FileTypeInfo,
    MutualExclusionGroup,
    ParserInfo,
)


class TestActionTypeFromString:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("store", ActionType.STORE),
            ("store_const", ActionType.STORE_CONST),
            ("store_true", ActionType.STORE_TRUE),
            ("store_false", ActionType.STORE_FALSE),
            ("append", ActionType.APPEND),
            ("append_const", ActionType.APPEND_CONST),
            ("count", ActionType.COUNT),
            ("help", ActionType.HELP),
            ("version", ActionType.VERSION),
            ("parsers", ActionType.PARSERS),
            ("extend", ActionType.EXTEND),
            ("boolean_optional", ActionType.BOOLEAN_OPTIONAL),
        ],
    )
    def test_valid(self, value, expected):
        assert ActionType.from_string(value) is expected

    def test_invalid_returns_unknown(self):
        assert ActionType.from_string("not_a_real_action") is ActionType.UNKNOWN

    def test_empty_string_returns_unknown(self):
        assert ActionType.from_string("") is ActionType.UNKNOWN


class TestActionInfoProperties:
    def test_is_optional_with_options(self):
        action = ActionInfo(
            option_strings=["--name"], dest="name", action_type=ActionType.STORE
        )
        assert action.is_optional is True

    def test_is_optional_without_options(self):
        action = ActionInfo(
            option_strings=[], dest="files", action_type=ActionType.STORE
        )
        assert action.is_optional is False

    def test_is_positional_without_options(self):
        action = ActionInfo(
            option_strings=[], dest="files", action_type=ActionType.STORE
        )
        assert action.is_positional is True

    def test_is_positional_with_options(self):
        action = ActionInfo(
            option_strings=["--name"], dest="name", action_type=ActionType.STORE
        )
        assert action.is_positional is False


class TestFileTypeInfo:
    def test_defaults(self):
        ft = FileTypeInfo()
        assert ft.mode == "r"
        assert ft.bufsize == -1
        assert ft.encoding is None
        assert ft.errors is None

    def test_custom(self):
        ft = FileTypeInfo(mode="rb", encoding="utf-8", errors="strict")
        assert ft.mode == "rb"
        assert ft.encoding == "utf-8"
        assert ft.errors == "strict"


class TestMutualExclusionGroup:
    def test_instantiation(self):
        meg = MutualExclusionGroup(required=True, actions=["--verbose", "--quiet"])
        assert meg.required is True
        assert meg.actions == ["--verbose", "--quiet"]


class TestArgumentGroup:
    def test_instantiation(self):
        ag = ArgumentGroup(
            title="output", description="Output options", actions=["--json", "--csv"]
        )
        assert ag.title == "output"
        assert ag.description == "Output options"
        assert ag.actions == ["--json", "--csv"]


class TestParserInfoGetActionByDest:
    def test_found(self):
        action = ActionInfo(
            option_strings=["--name"], dest="name", action_type=ActionType.STORE
        )
        parser = ParserInfo(actions=[action])
        assert parser.get_action_by_dest("name") is action

    def test_not_found(self):
        parser = ParserInfo(actions=[])
        assert parser.get_action_by_dest("missing") is None

    def test_returns_first_match(self):
        a1 = ActionInfo(option_strings=[], dest="x", action_type=ActionType.STORE)
        a2 = ActionInfo(option_strings=[], dest="x", action_type=ActionType.COUNT)
        parser = ParserInfo(actions=[a1, a2])
        assert parser.get_action_by_dest("x") is a1
