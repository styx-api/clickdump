# clickdump

Serialize [Click](https://click.palletsprojects.com/) commands and groups.

## Installation

```bash
pip install clickdump
```

## Usage

```python
import click
import clickdump

@click.command()
@click.option("-v", "--verbose", count=True, help="Verbosity")
@click.option("--name", default="world", help="Who to greet")
@click.argument("files", nargs=-1)
def cli(name, verbose, files):
    """A simple CLI tool."""

# Serialize to dict
data = clickdump.dump(cli)

# Serialize to JSON string
json_str = clickdump.dumps(cli, indent=2)
```

### Groups and subcommands

```python
@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    """A CLI with subcommands."""

@cli.command()
@click.option("--output", "-o", default="out.txt")
@click.argument("src")
def build(output, src):
    """Build the project."""

# Subcommand with parent for full program name
data = clickdump.dump(build, parent=cli)
# -> prog="cli build"
```

## JSON Schema

Output follows the same schema as [argdump](https://niwrap.dev/argdump/schema-v1.json)
(`$schema: https://niwrap.dev/argdump/schema-v1.json`).

## Features

- All Click parameter types: options, arguments, flags, counts, choices, paths, files
- Nested groups with subparsers (click.Group)
- Type introspection: builtins, Path, Choice, File, IntRange, FloatRange, DateTime, UUID, Tuple, and callable converters
- Click-specific extensions: `hidden`, `envvar`, `prompt`, `show_default`, `is_flag`, `count`, `multiple`, `flag_value`
- Program name resolution via parent tree traversal for nested subcommands
- Mutual exclusion and argument group serialization
- Environment metadata (`$env`) for reproducibility

## Options

```python
# Exclude environment metadata
clickdump.dump(cmd, include_env=False)

# Exclude hidden options
clickdump.dump(cmd, include_hidden=False)

# Compute full program name from parent group
clickdump.dump(subcmd, parent=root_group)

# Override the root program name
clickdump.dump(subcmd, parent=root_group, prog="mycli")
```

## Limitations

- This is a serialize-only library (no `load`/`loads` equivalent).
- Lambda and closure type converters cannot be fully serialized and will have `serializable: false`.
- Custom `click.ParamType` subclasses that are not standard built-in types may be marked as unknown.

## License

MIT
