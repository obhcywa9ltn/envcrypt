"""Flatten nested or prefixed env keys into a flat namespace."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional


class FlattenError(Exception):
    """Raised when flattening fails."""


def _parse_env(path: Path) -> Dict[str, str]:
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


def flatten_prefixes(
    path: Path,
    prefixes: List[str],
    separator: str = "_",
    dest: Optional[Path] = None,
    strip_prefix: bool = False,
) -> Dict[str, str]:
    """Return only keys that start with any of the given prefixes.

    If *strip_prefix* is True the prefix (and separator) is removed from the
    output key name.  If *dest* is provided the filtered pairs are written
    there.
    """
    if not path.exists():
        raise FlattenError(f"env file not found: {path}")
    if not prefixes:
        raise FlattenError("at least one prefix must be supplied")

    env = _parse_env(path)
    result: Dict[str, str] = {}
    for key, value in env.items():
        for prefix in prefixes:
            token = prefix if prefix.endswith(separator) else prefix + separator
            if key.startswith(token) or key == prefix:
                out_key = key[len(token):] if strip_prefix and key.startswith(token) else key
                result[out_key] = value
                break

    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{k}={v}\n" for k, v in result.items()]
        dest.write_text("".join(lines))

    return result


def list_prefixes(path: Path, separator: str = "_") -> List[str]:
    """Return the unique first-segment prefixes found in *path*."""
    if not path.exists():
        raise FlattenError(f"env file not found: {path}")
    env = _parse_env(path)
    seen: List[str] = []
    for key in env:
        if separator in key:
            prefix = key.split(separator, 1)[0]
            if prefix not in seen:
                seen.append(prefix)
    return seen
