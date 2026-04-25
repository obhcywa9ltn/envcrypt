"""Detect and remove duplicate keys from .env files."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


class DedupError(Exception):
    """Raised when deduplication fails."""


def _parse_lines(path: Path) -> List[str]:
    if not path.exists():
        raise DedupError(f"File not found: {path}")
    return path.read_text().splitlines(keepends=True)


def find_duplicates(env_file: Path) -> List[Tuple[str, List[int]]]:
    """Return a list of (key, [line_numbers]) for keys that appear more than once.

    Line numbers are 1-based.
    """
    lines = _parse_lines(env_file)
    seen: dict[str, List[int]] = {}
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        seen.setdefault(key, []).append(lineno)
    return [(k, v) for k, v in seen.items() if len(v) > 1]


def dedup_env_file(env_file: Path, dest: Path | None = None, keep: str = "last") -> int:
    """Remove duplicate keys from *env_file*, writing to *dest* (or in-place).

    *keep* must be ``'first'`` or ``'last'`` (default ``'last'``).

    Returns the number of duplicate lines removed.
    """
    if keep not in ("first", "last"):
        raise DedupError("keep must be 'first' or 'last'")

    lines = _parse_lines(env_file)

    # Collect positions of each key
    key_positions: dict[str, List[int]] = {}
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        key_positions.setdefault(key, []).append(idx)

    # Determine indices to drop
    drop: set[int] = set()
    for positions in key_positions.values():
        if len(positions) < 2:
            continue
        if keep == "last":
            drop.update(positions[:-1])
        else:
            drop.update(positions[1:])

    if not drop:
        return 0

    result = [line for idx, line in enumerate(lines) if idx not in drop]
    out = dest if dest is not None else env_file
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(result))
    return len(drop)
