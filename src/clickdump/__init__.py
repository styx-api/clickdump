"""clickdump - Serialize click commands and groups to JSON.

Usage:
    import click
    import clickdump

    @click.command()
    @click.option("-v", "--verbose", count=True)
    @click.option("--name", default="world")
    @click.argument("files", nargs=-1)
    def cli(name, verbose, files):
        ...

    # Serialize
    data = clickdump.dump(cli)      # -> dict
    json_str = clickdump.dumps(cli) # -> JSON string
"""

from ._serializer import dump, dumps
from .models import (
    ActionInfo,
    ActionType,
    ArgumentGroup,
    FileTypeInfo,
    MutualExclusionGroup,
    ParserInfo,
    TypeInfo,
)

__version__ = "0.1.0"

__all__ = [
    "dump",
    "dumps",
    "ActionType",
    "TypeInfo",
    "FileTypeInfo",
    "ActionInfo",
    "MutualExclusionGroup",
    "ArgumentGroup",
    "ParserInfo",
]
