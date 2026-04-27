"""Reorder keys in a .env file according to a specified order or alphabetically."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional


class ReorderError(Exception):
    """Raised when reordering fails."""


def _parse_lines(path: Path) -> List[str]:
    if not path.exists():
        raise ReorderError(f"File not found: {path}")
    return path.read_text().splitlines()


def _parse_env(lines: List[str]) -> dict:
    """Return ordered dict of key -> line index for KEY=VALUE lines."""
    result = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            result[key] = i
    return result


def reorder_env_file(
    src: Path,
    dest: Path,
    order: Optional[List[str]] = None,
    alphabetical: bool = False,
    reverse: bool = False,
) -> List[str]:
    """Reorder keys in *src* and write result to *dest*.

    If *order* is given, those keys appear first (in that order), followed by
    any remaining keys in their original relative order.  If *alphabetical* is
    True the full key list is sorted instead.  Returns the final key order.
    """
    lines = _parse_lines(src)
    key_to_idx = _parse_env(lines)

    if not key_to_idx:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("\n".join(lines))
        return []

    all_keys = list(key_to_idx.keys())

    if alphabetical:
        ordered_keys = sorted(all_keys, reverse=reverse)
    elif order:
        unknown = [k for k in order if k not in key_to_idx]
        if unknown:
            raise ReorderError(f"Unknown keys in order list: {unknown}")
        remaining = [k for k in all_keys if k not in order]
        ordered_keys = list(order) + remaining
        if reverse:
            ordered_keys = list(reversed(ordered_keys))
    else:
        raise ReorderError("Provide either 'order' list or set alphabetical=True")

    # Collect non-key lines (comments, blanks) and key lines separately
    non_key_lines = [
        line for line in lines
        if not line.strip() or line.strip().startswith("#") or "=" not in line.strip()
    ]
    key_lines = {key: lines[idx] for key, idx in key_to_idx.items()}

    out_lines = [key_lines[k] for k in ordered_keys]
    # Prepend any leading comments/blanks
    header = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            header.append(line)
        else:
            break

    final_lines = header + out_lines
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(final_lines) + "\n")
    return ordered_keys


def list_keys(src: Path) -> List[str]:
    """Return the keys present in *src* in their current order."""
    lines = _parse_lines(src)
    return list(_parse_env(lines).keys())
