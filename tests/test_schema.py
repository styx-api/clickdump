"""Tests for argdump schema validation."""

from __future__ import annotations

import pytest
import clickdump
from jsonschema import Draft202012Validator


class TestSchemaValidates:
    @pytest.mark.parametrize(
        "fixture_name",
        [
            "simple_command",
            "command_with_types",
            "simple_group",
            "nested_group",
            "command_with_hidden",
            "command_with_envvar",
            "command_no_help",
            "deprecated_command",
            "chain_group",
            "command_prompt_true",
            "command_required",
            "empty_command",
        ],
    )
    def test_schema_validates(self, argdump_schema, request, fixture_name):
        cli = request.getfixturevalue(fixture_name)
        data = clickdump.dump(cli, include_env=False)
        Draft202012Validator(argdump_schema).validate(data)

    def test_schema_with_env(self, argdump_schema, simple_command):
        data = clickdump.dump(simple_command, include_env=True)
        Draft202012Validator(argdump_schema).validate(data)
