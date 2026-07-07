"""Serialize click commands and groups to dict/JSON."""

from __future__ import annotations

import json
import platform
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import click

from ._types import type_info_from_param_type
from ._values import serialize_value
from .models import (
    ActionInfo,
    ActionType,
    ArgumentGroup,
    MutualExclusionGroup,
    ParserInfo,
)

SCHEMA_URL_V1 = "https://niwrap.dev/argdump/schema-v1.json"

_HELP_OPTION_NAMES = ["--help"]


def _classify_param(param: click.Parameter) -> tuple:
    """Determine ActionType for a Click Parameter.

    Returns:
        Tuple of (action_type, custom_action_class_or_None)
    """
    if isinstance(param, click.Argument):
        return ActionType.STORE, None

    if isinstance(param, click.Option):
        if param.count:
            return ActionType.COUNT, None
        if param.is_flag and param.secondary_opts:
            return ActionType.BOOLEAN_OPTIONAL, None
        if param.is_flag and param.is_bool_flag:
            return ActionType.STORE_TRUE, None
        if param.is_flag:
            return ActionType.STORE_CONST, None
        if param.multiple:
            return ActionType.APPEND, None
        return ActionType.STORE, None

    return ActionType.UNKNOWN, None


def _is_help_param(param: click.Parameter) -> bool:
    """Check if a parameter is Click's auto-generated help option."""
    if not isinstance(param, click.Option):
        return False
    if not param.opts:
        return False
    return any(o in _HELP_OPTION_NAMES for o in param.opts)


def _classify_nargs(param: click.Parameter, action_type: ActionType) -> Any:
    """Map Click nargs to argdump-compatible nargs."""
    if action_type in (
        ActionType.STORE_TRUE,
        ActionType.STORE_FALSE,
        ActionType.STORE_CONST,
        ActionType.COUNT,
        ActionType.BOOLEAN_OPTIONAL,
    ):
        return None

    nargs = param.nargs
    if nargs is None or nargs == 1:
        return None
    if nargs == -1:
        return "*"
    return nargs


def _extract_param_info(param: click.Parameter) -> ActionInfo:
    """Convert a Click Parameter to ActionInfo."""
    action_type, custom_class = _classify_param(param)
    type_info, file_type_info, choices = type_info_from_param_type(param.type)

    default = serialize_value(param.default) if param.default is not None else None

    # Positional arguments (click.Argument) must have empty option_strings
    # to match argdump's schema. Only click.Option should have real option strings.
    option_strings = list(param.opts) if isinstance(param, click.Option) else []

    info = ActionInfo(
        option_strings=option_strings,
        dest=param.name or "",
        action_type=action_type,
        nargs=_classify_nargs(param, action_type),
        default=default if default is not None else None,
        type_info=type_info,
        file_type_info=file_type_info,
        choices=choices,
        required=param.required,
        help=getattr(param, "help", None),
        metavar=param.metavar,
        custom_action_class=custom_class,
    )

    if isinstance(param, click.Option):
        info.hidden = param.hidden
        info.show_default = getattr(param, "show_default", None)
        info.show_envvar = getattr(param, "show_envvar", False)
        info.prompt = getattr(param, "prompt", None)
        info.is_flag = param.is_flag
        info.multiple = param.multiple

        if param.is_flag or param.count:
            raw_flag_value = getattr(param, "flag_value", None)
            info.flag_value = (
                serialize_value(raw_flag_value) if raw_flag_value is not None else None
            )
            if action_type == ActionType.COUNT:
                info.count = True
                info.default = 0 if info.default is None else info.default
            elif action_type == ActionType.STORE_CONST:
                info.const = serialize_value(raw_flag_value)

    # Shared for both Option and Argument
    info.envvar = param.envvar
    info.is_eager = param.is_eager
    info.expose_value = param.expose_value

    return info


def _create_help_action(cmd: click.Command) -> Optional[ActionInfo]:
    """Create a synthetic HELP action for auto-generated --help."""
    if not getattr(cmd, "add_help_option", True):
        return None

    return ActionInfo(
        option_strings=_HELP_OPTION_NAMES,
        dest="help",
        action_type=ActionType.HELP,
        help="Show this message and exit.",
        required=False,
    )


def _extract_command_actions(cmd: click.Command, include_hidden: bool = True) -> tuple:
    """Extract actions from a click Command.

    Args:
        cmd: The click Command to extract actions from.
        include_hidden: Whether to include hidden options.

    Returns:
        Tuple of (actions_list, argument_groups_list, mutex_groups_list)
    """
    actions: List[ActionInfo] = []
    action_to_dest: Dict[int, str] = {}

    params = list(cmd.params)

    help_action = _create_help_action(cmd)
    if help_action is not None:
        actions.append(help_action)

    for param in params:
        if _is_help_param(param):
            continue
        if not include_hidden and getattr(param, "hidden", False):
            continue
        action_info = _extract_param_info(param)
        actions.append(action_info)
        action_to_dest[id(param)] = param.name or ""

    return actions, [], []


def _create_parser_info(
    cmd: click.Command, *, prog_override: Optional[str] = None
) -> ParserInfo:
    """Create base ParserInfo from a Click Command."""
    info = ParserInfo(
        prog=prog_override or cmd.name,
        description=cmd.help,
        epilog=getattr(cmd, "epilog", None),
        add_help=getattr(cmd, "add_help_option", True),
    )

    # Click-specific extensions
    info.short_help = getattr(cmd, "short_help", None)
    info.hidden = getattr(cmd, "hidden", False)
    info.deprecated = getattr(cmd, "deprecated", False)
    info.no_args_is_help = getattr(cmd, "no_args_is_help", False)

    if hasattr(cmd, "allow_extra_args"):
        info.allow_extra_args = cmd.allow_extra_args
    if hasattr(cmd, "allow_interspersed_args"):
        info.allow_interspersed_args = cmd.allow_interspersed_args
    if hasattr(cmd, "ignore_unknown_options"):
        info.ignore_unknown_options = cmd.ignore_unknown_options

    if isinstance(cmd, click.Group):
        info.invoke_without_command = getattr(cmd, "invoke_without_command", False)
        info.chain = getattr(cmd, "chain", False)
        info.subcommand_metavar = getattr(cmd, "subcommand_metavar", None)

    return info


def serialize_command(
    cmd: click.Command,
    include_hidden: bool = True,
    *,
    prog_override: Optional[str] = None,
) -> ParserInfo:
    """Serialize a click Command to ParserInfo."""
    info = _create_parser_info(cmd, prog_override=prog_override)
    actions, _, _ = _extract_command_actions(cmd, include_hidden=include_hidden)
    info.actions = actions
    return info


def serialize_group(
    group: click.Group,
    include_hidden: bool = True,
    *,
    prog_override: Optional[str] = None,
) -> ParserInfo:
    """Serialize a click Group to ParserInfo.

    The group's own params are serialized as regular actions.
    Subcommands are serialized as a synthetic PARSERS action.
    """
    info = _create_parser_info(group, prog_override=prog_override)
    actions, _, _ = _extract_command_actions(group, include_hidden=include_hidden)

    if group.commands:
        subparser_action = _build_subparsers_action(
            group, include_hidden=include_hidden
        )
        actions.append(subparser_action)

    info.actions = actions
    return info


def _build_subparsers_action(
    group: click.Group, include_hidden: bool = True
) -> ActionInfo:
    """Build a synthetic PARSERS action for a Group's subcommands."""
    subparsers: Dict[str, Any] = {}
    subparsers_aliases: Dict[str, List[str]] = {}
    serialized_parsers: Dict[int, str] = {}
    parser_to_names: Dict[int, List[str]] = {}

    for name, cmd in group.commands.items():
        if cmd.name is None:
            continue
        if not include_hidden and getattr(cmd, "hidden", False):
            continue
        parser_id = id(cmd)
        if parser_id not in parser_to_names:
            parser_to_names[parser_id] = []
        parser_to_names[parser_id].append(name)

    for name, cmd in group.commands.items():
        if cmd.name is None:
            continue
        if not include_hidden and getattr(cmd, "hidden", False):
            continue
        parser_id = id(cmd)

        if parser_id in serialized_parsers:
            continue

        serialized_parsers[parser_id] = name

        if isinstance(cmd, click.Group):
            subparsers[name] = serialize_group(cmd, include_hidden=include_hidden)
        else:
            subparsers[name] = serialize_command(cmd, include_hidden=include_hidden)

        all_names = parser_to_names[parser_id]
        aliases = [n for n in all_names if n != name]
        if aliases:
            subparsers_aliases[name] = aliases

    return ActionInfo(
        option_strings=[],
        dest="command",
        action_type=ActionType.PARSERS,
        subparsers=subparsers,
        subparsers_title="Commands",
        subparsers_required=True,
        subparsers_aliases=subparsers_aliases if subparsers_aliases else None,
        help="Available subcommands",
    )


def _get_clickdump_version() -> str:
    try:
        from . import __version__

        return __version__
    except ImportError:
        return "unknown"


def _get_environment_info() -> Dict[str, str]:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "argdump_version": _get_clickdump_version(),
    }


def _extract_help_option_names(cmd: click.Command) -> None:
    """Populate HELP_OPTION_NAMES if a context is available, otherwise use defaults."""
    global _HELP_OPTION_NAMES
    try:
        ctx = click.Context(cmd)
        _HELP_OPTION_NAMES = list(ctx.help_option_names)
    except Exception:
        pass


def _serialize(
    cmd: click.Command,
    include_hidden: bool = True,
    *,
    prog_override: Optional[str] = None,
) -> ParserInfo:
    """Serialize any click Command or Group."""
    _extract_help_option_names(cmd)
    if isinstance(cmd, click.Group):
        return serialize_group(
            cmd, include_hidden=include_hidden, prog_override=prog_override
        )
    return serialize_command(
        cmd, include_hidden=include_hidden, prog_override=prog_override
    )


def _asdict_omit_defaults(obj: Any) -> Any:
    """Convert dataclass to dict, omitting fields with default values."""
    if not is_dataclass(obj) or isinstance(obj, type):
        return obj

    result = {}
    for f in fields(obj):
        value = getattr(obj, f.name)

        if f.default is not MISSING:
            default = f.default
        elif f.default_factory is not MISSING:
            default = f.default_factory()
        else:
            default = MISSING

        if default is not MISSING and value == default:
            continue

        if is_dataclass(value) and not isinstance(value, type):
            value = _asdict_omit_defaults(value)
        elif isinstance(value, list):
            value = [
                (
                    _asdict_omit_defaults(v)
                    if is_dataclass(v) and not isinstance(v, type)
                    else v
                )
                for v in value
            ]
        elif isinstance(value, dict):
            value = {
                k: (
                    _asdict_omit_defaults(v)
                    if is_dataclass(v) and not isinstance(v, type)
                    else v
                )
                for k, v in value.items()
            }

        result[f.name] = value

    return result


class _Encoder(json.JSONEncoder):
    """JSON encoder for dataclasses and enums."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return o.value
        if is_dataclass(o) and not isinstance(o, type):
            return _asdict_omit_defaults(o)
        return serialize_value(o)


def _find_command_path(
    root: click.Command, target: click.Command
) -> Optional[List[str]]:
    """Search root's command tree for target, returning the full name path.

    Returns list of names from root to target (e.g. ["cli", "config", "get"]),
    or None if target is not found under root.
    """
    stack: List[tuple] = [(root, [getattr(root, "name", "")])]

    while stack:
        node, path = stack.pop()

        if node is target:
            return path

        commands = getattr(node, "commands", {})
        for name, cmd in commands.items():
            if cmd.name is None:
                continue
            stack.append((cmd, [*path, cmd.name]))

    return None


def dump(
    cmd: click.Command,
    *,
    include_env: bool = True,
    include_hidden: bool = True,
    parent: Optional[click.Command] = None,
    prog: Optional[str] = None,
) -> Dict[str, Any]:
    """Serialize a click Command or Group to a dictionary.

    Args:
        cmd: The click Command or Group to serialize.
        include_env: Whether to include environment metadata.
        include_hidden: Whether to include hidden options (default True).
        parent: Parent group. The command tree under parent is crawled
               to find cmd and compute the full program name.
               E.g. passing parent=cli for nested subcommand "get"
               yields prog="cli config get".
        prog: Overrides the root (first) name in the computed program path.

    Returns:
        Dictionary representation compatible with argdump's schema.
    """
    if parent is not None:
        path = _find_command_path(parent, cmd)
        if path is not None:
            if prog is not None:
                path[0] = prog
            prog = " ".join(path)
    info = _serialize(cmd, include_hidden=include_hidden, prog_override=prog)
    data: Dict[str, Any] = json.loads(json.dumps(info, cls=_Encoder))

    result: Dict[str, Any] = {"$schema": SCHEMA_URL_V1}

    if include_env:
        result["$env"] = _get_environment_info()

    result.update(data)
    return result


def dumps(
    cmd: click.Command,
    *,
    include_env: bool = True,
    include_hidden: bool = True,
    parent: Optional[click.Command] = None,
    prog: Optional[str] = None,
    **json_kwargs: Any,
) -> str:
    """Serialize a click Command or Group to a JSON string.

    Args:
        cmd: The click Command or Group to serialize.
        include_env: Whether to include environment metadata.
        include_hidden: Whether to include hidden options (default True).
        parent: Parent group for computing the full program name.
        prog: Overrides the root (first) name in the computed program path.
        **json_kwargs: Additional arguments passed to json.dumps (e.g. indent).

    Returns:
        JSON string representation.
    """
    return json.dumps(
        dump(
            cmd,
            include_env=include_env,
            include_hidden=include_hidden,
            parent=parent,
            prog=prog,
        ),
        **json_kwargs,
    )
