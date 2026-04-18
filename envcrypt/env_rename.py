"""Rename keys inside a .env file."""
from __future__ import annotations

import re
from pathlib import Path


class RenameError(Exception):
    pass


def _parse_lines(path: Path) -> list[str]:
    if not path.exists():
        raise RenameError(f"File not found: {path}")
    return path.read_text().splitlines(keepends=True)


def rename_key(src: Path, old_key: str, new_key: str, dest: Path | None = None) -> Path:
    """Rename *old_key* to *new_key* in *src* and write result to *dest*.

    If *dest* is None the file is updated in-place.
    Raises RenameError when *old_key* is not found or *new_key* already exists.
    """
    lines = _parse_lines(src)
    key_pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")

    found_old = False
    for line in lines:
        m = key_pattern.match(line)
        if m and m.group(1) == new_key:
            raise RenameError(f"Key already exists: {new_key}")
        if m and m.group(1) == old_key:
            found_old = True

    if not found_old:
        raise RenameError(f"Key not found: {old_key}")

    out_lines: list[str] = []
    for line in lines:
        m = key_pattern.match(line)
        if m and m.group(1) == old_key:
            line = line.replace(old_key, new_key, 1)
        out_lines.append(line)

    target = dest or src
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(out_lines))
    return target


def list_keys(src: Path) -> list[str]:
    """Return all key names defined in *src*."""
    lines = _parse_lines(src)
    keys: list[str] = []
    key_pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")
    for line in lines:
        m = key_pattern.match(line)
        if m:
            keys.append(m.group(1))
    return keys
