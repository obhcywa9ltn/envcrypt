"""Mask (partially redact) env variable values for safe display."""
from __future__ import annotations

from pathlib import Path


class MaskError(Exception):
    pass


def _parse_env(path: Path) -> list[tuple[str, str, str]]:
    """Return list of (raw_line, key, value) tuples."""
    lines = []
    for raw in path.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            lines.append((raw, "", ""))
            continue
        key, _, value = stripped.partition("=")
        lines.append((raw, key.strip(), value.strip()))
    return lines


def mask_value(value: str, visible: int = 4, char: str = "*") -> str:
    """Return value with all but the last `visible` characters masked."""
    if len(value) <= visible:
        return char * len(value)
    return char * (len(value) - visible) + value[-visible:]


def mask_env_file(
    src: Path,
    dest: Path | None = None,
    keys: list[str] | None = None,
    visible: int = 4,
    char: str = "*",
) -> dict[str, str]:
    """Write a masked copy of *src* to *dest* (or src.masked if omitted).

    Returns a mapping of key -> masked_value for every masked key.
    """
    if not src.exists():
        raise MaskError(f"env file not found: {src}")

    dest = dest or src.with_suffix(".masked")
    dest.parent.mkdir(parents=True, exist_ok=True)

    entries = _parse_env(src)
    masked: dict[str, str] = {}
    out_lines: list[str] = []

    for raw, key, value in entries:
        if not key:
            out_lines.append(raw)
            continue
        if keys is None or key in keys:
            mv = mask_value(value, visible=visible, char=char)
            masked[key] = mv
            out_lines.append(f"{key}={mv}")
        else:
            out_lines.append(raw)

    dest.write_text("\n".join(out_lines) + "\n")
    return masked


def show_masked(src: Path, keys: list[str] | None = None, visible: int = 4) -> dict[str, str]:
    """Return masked values without writing a file."""
    if not src.exists():
        raise MaskError(f"env file not found: {src}")
    result: dict[str, str] = {}
    for _, key, value in _parse_env(src):
        if not key:
            continue
        if keys is None or key in keys:
            result[key] = mask_value(value, visible=visible)
    return result
