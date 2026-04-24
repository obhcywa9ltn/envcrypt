"""Promote .env values from one environment to another (e.g. staging -> production)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional


class PromoteError(Exception):
    """Raised when promotion fails."""


def _parse_env(path: Path) -> Dict[str, str]:
    """Parse key=value pairs from an env file, ignoring comments and blanks."""
    result: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


def _write_env(path: Path, pairs: Dict[str, str]) -> None:
    """Write key=value pairs to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in pairs.items()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def promote_keys(
    src: Path,
    dest: Path,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Copy selected keys (or all keys) from *src* env file into *dest* env file.

    Returns a mapping of the keys that were actually promoted.

    Raises:
        PromoteError: if src is missing, a requested key is absent, or a key
            already exists in dest and *overwrite* is False.
    """
    if not src.exists():
        raise PromoteError(f"Source env file not found: {src}")

    src_pairs = _parse_env(src)
    dest_pairs = _parse_env(dest) if dest.exists() else {}

    if keys is None:
        keys = list(src_pairs.keys())

    promoted: Dict[str, str] = {}
    for key in keys:
        if key not in src_pairs:
            raise PromoteError(f"Key '{key}' not found in source: {src}")
        if key in dest_pairs and not overwrite:
            raise PromoteError(
                f"Key '{key}' already exists in destination (use overwrite=True to replace)"
            )
        promoted[key] = src_pairs[key]

    dest_pairs.update(promoted)
    _write_env(dest, dest_pairs)
    return promoted


def list_promotable_keys(src: Path, dest: Path) -> Dict[str, List[str]]:
    """Return keys categorised as 'new' (absent in dest) or 'existing' (present in dest).

    Raises:
        PromoteError: if src is missing.
    """
    if not src.exists():
        raise PromoteError(f"Source env file not found: {src}")

    src_keys = set(_parse_env(src).keys())
    dest_keys = set(_parse_env(dest).keys()) if dest.exists() else set()

    return {
        "new": sorted(src_keys - dest_keys),
        "existing": sorted(src_keys & dest_keys),
    }
