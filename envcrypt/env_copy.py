"""Copy keys between .env files."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional


class CopyError(Exception):
    pass


def _parse_env(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value
    return result


def copy_keys(
    src: Path,
    dest: Path,
    keys: List[str],
    overwrite: bool = False,
) -> List[str]:
    """Copy specific keys from src into dest. Returns list of copied keys."""
    if not src.exists():
        raise CopyError(f"Source file not found: {src}")
    if not dest.exists():
        raise CopyError(f"Destination file not found: {dest}")

    src_data = _parse_env(src)
    dest_data = _parse_env(dest)

    missing = [k for k in keys if k not in src_data]
    if missing:
        raise CopyError(f"Keys not found in source: {', '.join(missing)}")

    if not overwrite:
        conflicts = [k for k in keys if k in dest_data]
        if conflicts:
            raise CopyError(
                f"Keys already exist in destination (use overwrite=True): {', '.join(conflicts)}"
            )

    dest_lines = dest.read_text().splitlines(keepends=True)
    copied: List[str] = []

    for key in keys:
        value = src_data[key]
        new_line = f"{key}={value}\n"
        if overwrite and key in dest_data:
            dest_lines = [
                new_line if line.startswith(f"{key}=") else line
                for line in dest_lines
            ]
        else:
            dest_lines.append(new_line)
        copied.append(key)

    dest.write_text("".join(dest_lines))
    return copied


def copy_all(
    src: Path,
    dest: Path,
    overwrite: bool = False,
) -> List[str]:
    """Copy all keys from src into dest."""
    if not src.exists():
        raise CopyError(f"Source file not found: {src}")
    src_data = _parse_env(src)
    return copy_keys(src, dest, list(src_data.keys()), overwrite=overwrite)
