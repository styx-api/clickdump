"""Data models for click CLI serialization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class ActionType(str, Enum):
    """Click action types (mirrors argdump.ActionType for schema compat)."""

    STORE = "store"
    STORE_CONST = "store_const"
    STORE_TRUE = "store_true"
    STORE_FALSE = "store_false"
    APPEND = "append"
    APPEND_CONST = "append_const"
    COUNT = "count"
    HELP = "help"
    VERSION = "version"
    PARSERS = "parsers"
    EXTEND = "extend"
    BOOLEAN_OPTIONAL = "boolean_optional"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "ActionType":
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


@dataclass
class TypeInfo:
    """Type converter information."""

    name: str
    module: Optional[str] = None
    builtin: bool = False
    serializable: bool = True


@dataclass
class FileTypeInfo:
    """File type parameters (like argparse.FileType / click.File)."""

    mode: str = "r"
    bufsize: int = -1
    encoding: Optional[str] = None
    errors: Optional[str] = None


@dataclass
class ActionInfo:
    """Serialized Click Parameter (Option or Argument)."""

    option_strings: List[str]
    dest: str
    action_type: ActionType
    nargs: Union[str, int, None] = None
    const: Any = None
    default: Any = None
    type_info: Optional[TypeInfo] = None
    file_type_info: Optional[FileTypeInfo] = None
    choices: Optional[List[Any]] = None
    required: bool = False
    help: Optional[str] = None
    metavar: Union[str, Tuple[str, ...], None] = None
    deprecated: bool = False
    version: Optional[str] = None
    subparsers: Optional[Dict[str, "ParserInfo"]] = None
    subparsers_title: Optional[str] = None
    subparsers_description: Optional[str] = None
    subparsers_dest: Optional[str] = None
    subparsers_required: bool = False
    subparsers_aliases: Optional[Dict[str, List[str]]] = None
    custom_action_class: Optional[str] = None

    # Click-specific extensions
    hidden: bool = False
    show_default: Optional[Union[bool, str]] = None
    show_envvar: bool = False
    prompt: Optional[Union[bool, str]] = None
    envvar: Optional[Union[str, List[str]]] = None
    is_eager: bool = False
    expose_value: bool = True
    count: bool = False
    is_flag: bool = False
    flag_value: Any = None
    multiple: bool = False

    @property
    def is_optional(self) -> bool:
        return bool(self.option_strings)

    @property
    def is_positional(self) -> bool:
        return not self.option_strings


@dataclass
class MutualExclusionGroup:
    """Mutually exclusive argument group."""

    required: bool
    actions: List[str]


@dataclass
class ArgumentGroup:
    """Argument group for help organization."""

    title: Optional[str]
    description: Optional[str]
    actions: List[str]


@dataclass
class ParserInfo:
    """Complete serialized Click Command or Group."""

    prog: Optional[str] = None
    description: Optional[str] = None
    epilog: Optional[str] = None
    usage: Optional[str] = None
    add_help: bool = True
    allow_abbrev: bool = True
    formatter_class: Optional[str] = None
    prefix_chars: str = "-"
    fromfile_prefix_chars: Optional[str] = None
    argument_default: Any = None
    conflict_handler: str = "error"
    exit_on_error: bool = True
    suggest_on_error: bool = False
    color: bool = True

    actions: List[ActionInfo] = field(default_factory=list)
    argument_groups: List[ArgumentGroup] = field(default_factory=list)
    mutually_exclusive_groups: List[MutualExclusionGroup] = field(default_factory=list)

    # Click-specific extensions
    short_help: Optional[str] = None
    hidden: bool = False
    deprecated: bool = False
    no_args_is_help: bool = False
    invoke_without_command: bool = False
    chain: bool = False
    subcommand_metavar: Optional[str] = None
    allow_extra_args: bool = False
    allow_interspersed_args: bool = True
    ignore_unknown_options: bool = False

    def get_action_by_dest(self, dest: str) -> Optional[ActionInfo]:
        for action in self.actions:
            if action.dest == dest:
                return action
        return None
