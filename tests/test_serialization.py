"""Tests for clickdump serialization."""

from __future__ import annotations

import json

import click
import clickdump


class TestSimpleCommand:
    def test_dump_returns_dict(self, simple_command):
        result = clickdump.dump(simple_command)
        assert isinstance(result, dict)

    def test_dumps_returns_string(self, simple_command):
        result = clickdump.dumps(simple_command)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_schema_key(self, simple_command):
        result = clickdump.dump(simple_command)
        assert "$schema" in result
        assert result["$schema"] == "https://niwrap.dev/argdump/schema-v1.json"

    def test_env_key(self, simple_command):
        result = clickdump.dump(simple_command, include_env=True)
        assert "$env" in result

    def test_no_env_when_disabled(self, simple_command):
        result = clickdump.dump(simple_command, include_env=False)
        assert "$env" not in result

    def test_prog_from_command_name(self, simple_command):
        result = clickdump.dump(simple_command)
        assert result["prog"] == "cli"

    def test_description_from_docstring(self, simple_command):
        result = clickdump.dump(simple_command)
        assert result["description"] == "A simple CLI tool."

    def test_has_help_action(self, simple_command):
        result = clickdump.dump(simple_command)
        actions = result["actions"]
        help_actions = [a for a in actions if a["action_type"] == "help"]
        assert len(help_actions) == 1
        assert help_actions[0]["option_strings"] == ["--help"]

    def test_count_action(self, simple_command):
        result = clickdump.dump(simple_command)
        actions = result["actions"]
        verbose = [a for a in actions if a["dest"] == "verbose"]
        assert len(verbose) == 1
        assert verbose[0]["action_type"] == "count"
        assert verbose[0]["default"] == 0
        assert verbose[0]["count"] is True

    def test_store_action(self, simple_command):
        result = clickdump.dump(simple_command)
        actions = result["actions"]
        name = [a for a in actions if a["dest"] == "name"]
        assert len(name) == 1
        assert name[0]["action_type"] == "store"
        assert name[0]["default"] == "world"

    def test_argument_as_store(self, simple_command):
        result = clickdump.dump(simple_command)
        actions = result["actions"]
        files = [a for a in actions if a["dest"] == "files"]
        assert len(files) == 1
        assert files[0]["action_type"] == "store"
        assert files[0]["nargs"] == "*"
        assert files[0].get("required", False) is False


class TestTypes:
    def test_int_type(self, command_with_types):
        result = clickdump.dump(command_with_types)
        actions = result["actions"]
        count = [a for a in actions if a["dest"] == "count"][0]
        assert count["type_info"]["name"] == "int"
        assert count["type_info"]["module"] == "builtins"
        assert count["type_info"]["builtin"] is True

    def test_float_type(self, command_with_types):
        result = clickdump.dump(command_with_types)
        actions = result["actions"]
        pi = [a for a in actions if a["dest"] == "pi"][0]
        assert pi["type_info"]["name"] == "float"

    def test_boolean_flag(self, command_with_types):
        result = clickdump.dump(command_with_types)
        actions = result["actions"]
        flag = [a for a in actions if a["dest"] == "flag"][0]
        assert flag["action_type"] == "boolean_optional"
        assert flag["default"] is True

    def test_is_flag_option(self, command_with_types):
        result = clickdump.dump(command_with_types)
        actions = result["actions"]
        switch = [a for a in actions if a["dest"] == "switch"][0]
        assert switch["action_type"] == "store_true"
        assert switch["default"] is False

    def test_choice_type(self, command_with_types):
        result = clickdump.dump(command_with_types)
        actions = result["actions"]
        color = [a for a in actions if a["dest"] == "color"][0]
        assert color["type_info"]["name"] == "choice"
        assert color["choices"] == ["red", "green", "blue"]

    def test_path_type(self, command_with_types):
        result = clickdump.dump(command_with_types)
        actions = result["actions"]
        path = [a for a in actions if a["dest"] == "path"][0]
        assert path["type_info"]["name"] == "Path"
        assert path["type_info"]["module"] == "pathlib"


class TestEnvvar:
    def test_envvar_option(self, command_with_envvar):
        result = clickdump.dump(command_with_envvar)
        actions = result["actions"]
        host = [a for a in actions if a["dest"] == "host"][0]
        assert host["envvar"] == "HOST"


class TestHidden:
    def test_hidden_option_is_omitted(self, command_with_hidden):
        result = clickdump.dump(command_with_hidden, include_hidden=False)
        actions = result["actions"]
        hidden = [a for a in actions if a["dest"] == "hidden"]
        assert len(hidden) == 0

    def test_hidden_option_included_by_default(self, command_with_hidden):
        result = clickdump.dump(command_with_hidden)
        actions = result["actions"]
        hidden = [a for a in actions if a["dest"] == "hidden"]
        assert len(hidden) == 1

    def test_visible_option_included(self, command_with_hidden):
        result = clickdump.dump(command_with_hidden)
        actions = result["actions"]
        visible = [a for a in actions if a["dest"] == "visible"]
        assert len(visible) == 1
        assert visible[0]["action_type"] == "store"


class TestGroup:
    def test_group_has_subparsers(self, simple_group):
        result = clickdump.dump(simple_group)
        actions = result["actions"]
        parsers = [a for a in actions if a["action_type"] == "parsers"]
        assert len(parsers) == 1
        assert "build" in parsers[0]["subparsers"]
        assert "clean" in parsers[0]["subparsers"]

    def test_subcommand_has_params(self, simple_group):
        result = clickdump.dump(simple_group)
        actions = result["actions"]
        parsers = [a for a in actions if a["action_type"] == "parsers"][0]
        build = parsers["subparsers"]["build"]
        assert build["prog"] == "build"
        assert build["description"] == "Build the project."
        build_actions = build["actions"]
        dests = [a["dest"] for a in build_actions]
        assert "output" in dests
        assert "src" in dests

    def test_nested_group_subparsers(self, nested_group):
        result = clickdump.dump(nested_group)
        actions = result["actions"]
        parsers = [a for a in actions if a["action_type"] == "parsers"][0]
        assert "config" in parsers["subparsers"]
        config = parsers["subparsers"]["config"]
        config_actions = config["actions"]
        config_parsers = [a for a in config_actions if a["action_type"] == "parsers"]
        assert len(config_parsers) == 1
        assert "get" in config_parsers[0]["subparsers"]
        assert "set" in config_parsers[0]["subparsers"]

    def test_group_has_own_params(self, simple_group):
        result = clickdump.dump(simple_group)
        actions = result["actions"]
        debug = [a for a in actions if a["dest"] == "debug"]
        assert len(debug) == 1
        assert debug[0]["action_type"] == "boolean_optional"


class TestEnvironmentInfo:
    def test_env_fields(self, simple_command):
        result = clickdump.dump(simple_command)
        env = result["$env"]
        assert "python_version" in env
        assert "python_implementation" in env
        assert "platform_system" in env
        assert "argdump_version" in env
        assert env["argdump_version"] == "0.1.0"

    def test_dumps_indent(self, simple_command):
        result = clickdump.dumps(simple_command, indent=2)
        parsed = json.loads(result)
        assert parsed["prog"] == "cli"


class TestEdgeCases:
    def test_command_with_no_params(self):
        @click.command()
        def simple():
            """Simple command."""

        result = clickdump.dump(simple)
        assert result["prog"] == "simple"
        assert len(result["actions"]) == 1  # just help

    def test_command_with_multiple_options(self):
        @click.command()
        @click.option("--a", multiple=True, type=int)
        @click.option("--b", is_flag=True)
        @click.option("--c", flag_value="custom")
        def cli(a, b, c):
            """Multi options."""

        result = clickdump.dump(cli)
        actions = {a["dest"]: a for a in result["actions"]}
        assert actions["a"]["action_type"] == "append"
        assert actions["a"]["multiple"] is True
        assert actions["b"]["action_type"] == "store_true"
        assert actions["c"]["action_type"] == "store_const"
        assert actions["c"]["const"] == "custom"

    def test_json_round_trip(self, simple_command):
        json_str = clickdump.dumps(simple_command)
        parsed = json.loads(json_str)
        assert parsed["prog"] == "cli"
        assert len(parsed["actions"]) > 0


class TestProgramName:
    def test_parent_sets_prog(self, simple_group):
        build = simple_group.commands["build"]
        result = clickdump.dump(build, parent=simple_group)
        assert result["prog"] == "cli build"

    def test_prog_override(self, simple_group):
        build = simple_group.commands["build"]
        result = clickdump.dump(build, prog="custom")
        assert result["prog"] == "custom"

    def test_prog_overrides_parent(self, simple_group):
        build = simple_group.commands["build"]
        result = clickdump.dump(build, parent=simple_group, prog="mycli")
        assert result["prog"] == "mycli build"

    def test_no_parent_uses_cmd_name(self, simple_command):
        result = clickdump.dump(simple_command)
        assert result["prog"] == "cli"

    def test_nested_parent_crawls(self, nested_group):
        config = nested_group.commands["config"]
        get = config.commands.get("get")
        result = clickdump.dump(get, parent=nested_group)
        assert result["prog"] == "cli config get"

    def test_nested_immediate_parent(self, nested_group):
        config = nested_group.commands["config"]
        get = config.commands.get("get")
        result = clickdump.dump(get, parent=config)
        assert result["prog"] == "config get"

    def test_prog_overrides_root_only(self, nested_group):
        config = nested_group.commands["config"]
        get = config.commands.get("get")
        result = clickdump.dump(get, parent=nested_group, prog="mycli")
        assert result["prog"] == "mycli config get"

    def test_cmd_not_found_falls_back(self, nested_group):
        config = nested_group.commands["config"]

        @click.command()
        def standalone():
            pass

        # standalone is not under config, so parent lookup fails -> falls back to prog
        result = clickdump.dump(standalone, parent=config, prog="fallback")
        assert result["prog"] == "fallback"

    def test_prog_overrides_root_when_parent_found(self, nested_group):
        config = nested_group.commands["config"]
        get = config.commands.get("get")
        result = clickdump.dump(get, parent=config, prog="x")
        assert result["prog"] == "x get"

    def test_dumps_respects_parent(self, simple_group):
        build = simple_group.commands["build"]
        json_str = clickdump.dumps(build, parent=simple_group)
        parsed = __import__("json").loads(json_str)
        assert parsed["prog"] == "cli build"
