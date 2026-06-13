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
