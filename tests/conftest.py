"""Test fixtures for clickdump tests."""

from __future__ import annotations

import click
import pytest


@pytest.fixture
def simple_command():
    """Basic command with positional and optional args."""

    @click.command()
    @click.option("-v", "--verbose", count=True, help="Verbosity level")
    @click.option("--name", default="world", help="Who to greet")
    @click.argument("files", nargs=-1)
    def cli(name, verbose, files):
        """A simple CLI tool."""

    return cli


@pytest.fixture
def command_with_types():
    """Command with various Click types."""

    @click.command()
    @click.option("--count", type=int, default=1)
    @click.option("--pi", type=float)
    @click.option("--flag/--no-flag", default=True)
    @click.option("--switch", is_flag=True)
    @click.option("--color", type=click.Choice(["red", "green", "blue"]))
    @click.option("--path", type=click.Path(exists=True))
    @click.option("--num", type=click.IntRange(0, 100))
    def cli(count, pi, flag, switch, color, path, num):
        """Command with types."""

    return cli


@pytest.fixture
def command_with_envvar():
    """Command with envvar."""

    @click.command()
    @click.option("--host", envvar="HOST", default="localhost")
    @click.option("--port", envvar="PORT", type=int, default=8080)
    def cli(host, port):
        """Command with env vars."""

    return cli


@pytest.fixture
def command_with_hidden():
    """Command with hidden option."""

    @click.command()
    @click.option("--visible", help="I am visible")
    @click.option("--hidden", hidden=True, help="I am hidden")
    def cli(visible, hidden):
        """Command with hidden options."""

    return cli


@pytest.fixture
def simple_group():
    """Group with subcommands."""

    @click.group()
    @click.option("--debug/--no-debug", default=False)
    def cli(debug):
        """A CLI with subcommands."""

    @cli.command()
    @click.option("--output", "-o", default="out.txt")
    @click.argument("src")
    def build(output, src):
        """Build the project."""

    @cli.command()
    @click.option("--all", is_flag=True)
    def clean(all):
        """Clean the project."""

    return cli


@pytest.fixture
def nested_group():
    """Group with nested subcommands."""

    @click.group()
    def cli():
        """Top-level CLI."""

    @cli.group()
    @click.option("--format", type=click.Choice(["json", "yaml"]))
    def config(format):
        """Configuration commands."""

    @config.command()
    @click.argument("key")
    def get(key):
        """Get a config value."""

    @config.command()
    @click.argument("value")
    def set(value):
        """Set a config value."""

    return cli


@pytest.fixture
def command_no_help():
    """Command with add_help_option=False."""

    @click.command(add_help_option=False)
    def cli():
        """No help."""

    return cli


@pytest.fixture
def deprecated_command():
    """Command with deprecated=True."""

    @click.command(deprecated=True)
    def cli():
        """Deprecated command."""

    return cli


@pytest.fixture
def invoke_without_command_group():
    """Group with invoke_without_command=True."""

    @click.group(invoke_without_command=True)
    def cli():
        """Group."""

    @cli.command()
    def sub():
        """Sub."""

    return cli


@pytest.fixture
def chain_group():
    """Group with chain=True."""

    @click.group(chain=True)
    def cli():
        """Chain group."""

    @cli.command()
    def step_a():
        """Step A."""

    @cli.command()
    def step_b():
        """Step B."""

    return cli


@pytest.fixture
def metavar_group():
    """Group with subcommand_metavar."""

    @click.group(subcommand_metavar="COMMAND")
    def cli():
        """Group."""

    @cli.command()
    def sub():
        """Sub."""

    return cli


@pytest.fixture
def empty_group():
    """Group with no subcommands."""

    @click.group()
    def cli():
        """Empty group."""

    return cli


@pytest.fixture
def command_prompt_true():
    """Command with prompt=True."""

    @click.command()
    @click.option("--name", prompt=True)
    def cli(name):
        """Prompt."""

    return cli


@pytest.fixture
def command_prompt_string():
    """Command with prompt string."""

    @click.command()
    @click.option("--name", prompt="Enter name: ")
    def cli(name):
        """Prompt."""

    return cli


@pytest.fixture
def command_show_default():
    """Command with show_default=True."""

    @click.command()
    @click.option("--output", default="out.txt", show_default=True)
    def cli(output):
        """Show default."""

    return cli


@pytest.fixture
def command_show_envvar():
    """Command with show_envvar=True."""

    @click.command()
    @click.option("--host", envvar="HOST", show_envvar=True)
    def cli(host):
        """Show envvar."""

    return cli


@pytest.fixture
def command_is_eager():
    """Command with is_eager=True."""

    @click.command()
    @click.option("--verbose", is_eager=True)
    def cli(verbose):
        """Eager."""

    return cli


@pytest.fixture
def command_expose_false():
    """Command with expose_value=False."""

    @click.command()
    @click.option("--secret", expose_value=False)
    def cli(secret):
        """Hidden dest."""

    return cli


@pytest.fixture
def command_required():
    """Command with required=True."""

    @click.command()
    @click.option("--token", required=True)
    def cli(token):
        """Required."""

    return cli


@pytest.fixture
def command_metavar():
    """Command with metavar."""

    @click.command()
    @click.option("--config", metavar="FILE")
    def cli(config):
        """Metavar."""

    return cli


@pytest.fixture
def command_envvar_list():
    """Command with envvar list."""

    @click.command()
    @click.option("--host", envvar=["HOST", "SERVER_HOST"])
    def cli(host):
        """Envvar list."""

    return cli


@pytest.fixture
def group_with_aliases():
    """Group with aliased commands."""

    build_cmd = click.Command("build", help="Build it.")

    @click.group()
    def cli():
        """CLI."""

    cli.add_command(build_cmd, "build")
    cli.add_command(build_cmd, "compile")

    return cli


@pytest.fixture
def group_with_hidden_subcommand():
    """Group with a hidden subcommand."""

    @click.group()
    def cli():
        """CLI."""

    @cli.command(hidden=True)
    def secret():
        """Secret."""

    @cli.command()
    def visible():
        """Visible."""

    return cli
