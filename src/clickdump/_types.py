"""Type introspection for Click ParamType instances."""

from __future__ import annotations

from click import types as click_types

from .models import FileTypeInfo, TypeInfo


def type_info_from_param_type(param_type: click_types.ParamType) -> tuple:
    """Extract (TypeInfo, FileTypeInfo, choices) from a Click ParamType."""
    if isinstance(param_type, click_types.StringParamType):
        return TypeInfo(name="str", module="builtins", builtin=True), None, None

    if isinstance(param_type, click_types.IntRange):
        return TypeInfo(name="int_range", module="click.types"), None, None

    if isinstance(param_type, click_types.FloatRange):
        return TypeInfo(name="float_range", module="click.types"), None, None

    if isinstance(param_type, click_types.IntParamType):
        return TypeInfo(name="int", module="builtins", builtin=True), None, None

    if isinstance(param_type, click_types.FloatParamType):
        return TypeInfo(name="float", module="builtins", builtin=True), None, None

    if isinstance(param_type, click_types.BoolParamType):
        return TypeInfo(name="bool", module="builtins", builtin=True), None, None

    if isinstance(param_type, click_types.UUIDParameterType):
        return TypeInfo(name="UUID", module="uuid"), None, None

    if isinstance(param_type, click_types.UnprocessedParamType):
        return TypeInfo(name="str", module="builtins", builtin=True), None, None

    if isinstance(param_type, click_types.Choice):
        return (
            TypeInfo(name="choice", module="click.types"),
            None,
            list(param_type.choices),
        )

    if isinstance(param_type, click_types.DateTime):
        return TypeInfo(name="datetime", module="datetime"), None, None

    if isinstance(param_type, click_types.Path):
        return TypeInfo(name="Path", module="pathlib"), None, None

    if isinstance(param_type, click_types.File):
        file_info = FileTypeInfo(
            mode=getattr(param_type, "mode", "r"),
            encoding=getattr(param_type, "encoding", None),
            errors=getattr(param_type, "errors", "strict"),
        )
        return TypeInfo(name="FileType", module="click.types"), file_info, None

    if isinstance(param_type, click_types.Tuple):
        types = getattr(param_type, "types", [])
        name = "_".join(t.name for t in types) if types else "tuple"
        return TypeInfo(name=name, module="click.types"), None, None

    if isinstance(param_type, click_types.FuncParamType):
        func = getattr(param_type, "func", None)
        if func is not None:
            return _type_info_from_callable(func), None, None
        return TypeInfo(name="unknown", serializable=False), None, None

    return TypeInfo(name="unknown", serializable=False), None, None


def _type_info_from_callable(type_func) -> TypeInfo:
    """Extract TypeInfo from a Python callable type converter."""
    if type_func is None:
        return TypeInfo(name="str", module="builtins", builtin=True)

    builtin_types = (int, float, str, bool, complex, bytes, bytearray)
    if type_func in builtin_types:
        return TypeInfo(name=type_func.__name__, builtin=True)

    name = getattr(type_func, "__name__", None)
    module = getattr(type_func, "__module__", None)

    if name == "<lambda>":
        return TypeInfo(name="<lambda>", module=module, serializable=False)

    if name:
        serializable = module is not None and not name.startswith("<")
        return TypeInfo(name=name, module=module, serializable=serializable)

    return TypeInfo(name=repr(type_func), module=module, serializable=False)
