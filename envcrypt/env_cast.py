"""Type-casting utilities for .env values."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class CastError(Exception):
    """Raised when a cast or file operation fails."""


_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _parse_env(path: Path) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def cast_value(value: str, to: str) -> Any:
    """Cast *value* to the requested type name.

    Supported types: ``str``, ``int``, ``float``, ``bool``.
    Raises :class:`CastError` on failure.
    """
    if to == "str":
        return value
    if to == "int":
        try:
            return int(value)
        except ValueError:
            raise CastError(f"Cannot cast {value!r} to int")
    if to == "float":
        try:
            return float(value)
        except ValueError:
            raise CastError(f"Cannot cast {value!r} to float")
    if to == "bool":
        lower = value.lower()
        if lower in _BOOL_TRUE:
            return True
        if lower in _BOOL_FALSE:
            return False
        raise CastError(f"Cannot cast {value!r} to bool")
    raise CastError(f"Unknown target type: {to!r}")


def cast_env_file(path: Path, schema: dict[str, str]) -> dict[str, Any]:
    """Read *path* and cast each key listed in *schema* to its declared type.

    Keys absent from *schema* are returned as plain strings.
    Raises :class:`CastError` if *path* does not exist or a cast fails.
    """
    if not path.exists():
        raise CastError(f"Env file not found: {path}")
    raw = _parse_env(path)
    result: dict[str, Any] = {}
    for key, value in raw.items():
        target = schema.get(key, "str")
        result[key] = cast_value(value, target)
    return result


def infer_types(path: Path) -> dict[str, str]:
    """Return a best-guess type schema for every key in *path*.

    Raises :class:`CastError` if *path* does not exist.
    """
    if not path.exists():
        raise CastError(f"Env file not found: {path}")
    raw = _parse_env(path)
    schema: dict[str, str] = {}
    for key, value in raw.items():
        lower = value.lower()
        if lower in _BOOL_TRUE | _BOOL_FALSE:
            schema[key] = "bool"
        else:
            try:
                int(value)
                schema[key] = "int"
            except ValueError:
                try:
                    float(value)
                    schema[key] = "float"
                except ValueError:
                    schema[key] = "str"
    return schema
