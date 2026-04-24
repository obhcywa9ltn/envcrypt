"""Apply a patch (set/unset/update) of key-value pairs to an .env file."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PatchError(Exception):
    """Raised when a patch operation fails."""


def _parse_lines(path: Path) -> List[str]:
    """Return raw lines from *path*, or [] if missing."""
    if not path.exists():
        return []
    return path.read_text().splitlines(keepends=True)


def _parse_env(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for line in _parse_lines(path):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        env[key.strip()] = value.strip()
    return env


def patch_env_file(
    path: Path,
    updates: Optional[Dict[str, str]] = None,
    removals: Optional[List[str]] = None,
    dest: Optional[Path] = None,
) -> Tuple[int, int]:
    """Apply *updates* and *removals* to the env file at *path*.

    Returns (added_or_updated, removed) counts.
    Writes to *dest* if provided, otherwise overwrites *path*.
    Raises PatchError when *path* does not exist.
    """
    if not path.exists():
        raise PatchError(f"env file not found: {path}")

    updates = updates or {}
    removals = set(removals or [])

    lines = _parse_lines(path)
    existing_keys: Dict[str, int] = {}  # key -> line index
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.partition("=")[0].strip()
        existing_keys[key] = i

    # Apply removals and updates in-place
    new_lines = []
    processed_updates: set = set()
    removed = 0
    updated = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.partition("=")[0].strip()
        if key in removals:
            removed += 1
            continue
        if key in updates:
            new_lines.append(f"{key}={updates[key]}\n")
            processed_updates.add(key)
            updated += 1
        else:
            new_lines.append(line)

    # Append brand-new keys
    added = 0
    for key, value in updates.items():
        if key not in processed_updates:
            new_lines.append(f"{key}={value}\n")
            added += 1

    out = dest or path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(new_lines))
    return (updated + added, removed)


def list_patch_keys(path: Path) -> List[str]:
    """Return sorted list of keys defined in *path*."""
    if not path.exists():
        raise PatchError(f"env file not found: {path}")
    return sorted(_parse_env(path).keys())
