"""Utilities for normalising .env key casing."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


class UppercaseError(Exception):
    """Raised when a key-casing operation fails."""


def _parse_lines(path: Path) -> List[str]:
    if not path.exists():
        raise UppercaseError(f"File not found: {path}")
    return path.read_text().splitlines(keepends=True)


def list_non_uppercase_keys(src: Path) -> List[str]:
    """Return keys that are not already fully uppercase."""
    issues: List[str] = []
    for raw in _parse_lines(src):
        line = raw.rstrip("\n")
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key != key.upper():
            issues.append(key)
    return issues


def uppercase_env_file(
    src: Path,
    dest: Path | None = None,
) -> Tuple[Path, int]:
    """Rewrite *src* so that every key is uppercase.

    Writes to *dest* when provided, otherwise overwrites *src* in-place.
    Returns ``(dest_path, number_of_keys_changed)``.
    """
    lines = _parse_lines(src)
    out: List[str] = []
    changed = 0
    for raw in lines:
        line = raw.rstrip("\n")
        newline = raw[len(line):]
        if not line or line.lstrip().startswith("#") or "=" not in line:
            out.append(raw)
            continue
        key, value = line.split("=", 1)
        key_stripped = key.strip()
        upper = key_stripped.upper()
        if upper != key_stripped:
            changed += 1
            line = upper + "=" + value
        out.append(line + newline)
    target = dest if dest is not None else src
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(out))
    return target, changed
