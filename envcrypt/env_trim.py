"""Trim whitespace from .env file values."""
from __future__ import annotations

from pathlib import Path
from typing import Optional


class TrimError(Exception):
    """Raised when trimming fails."""


def _parse_lines(path: Path) -> list[str]:
    if not path.exists():
        raise TrimError(f"File not found: {path}")
    return path.read_text().splitlines(keepends=True)


def trim_env_file(
    src: Path,
    dest: Optional[Path] = None,
    *,
    keys: Optional[list[str]] = None,
) -> dict[str, str]:
    """Trim leading/trailing whitespace from values in *src*.

    If *keys* is given, only those keys are trimmed.  Writes the result
    to *dest* (defaults to *src* in-place).  Returns a mapping of
    ``{key: trimmed_value}`` for every key that was changed.
    """
    lines = _parse_lines(src)
    changed: dict[str, str] = {}
    out: list[str] = []

    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.startswith("#") or "=" not in stripped:
            out.append(line)
            continue

        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        if keys is None or key in keys:
            trimmed = raw_value.strip()
            if trimmed != raw_value:
                changed[key] = trimmed
                out.append(f"{key}={trimmed}\n")
                continue

        out.append(line)

    target = dest if dest is not None else src
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(out))
    return changed


def list_untrimmed_keys(src: Path) -> list[str]:
    """Return keys whose values have leading or trailing whitespace."""
    lines = _parse_lines(src)
    result: list[str] = []
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        if raw_value != raw_value.strip():
            result.append(key.strip())
    return result
