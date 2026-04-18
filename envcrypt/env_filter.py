"""Filter .env file keys by pattern or list."""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Optional


class FilterError(Exception):
    pass


def _parse_env(path: Path) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def filter_by_keys(env_file: Path, keys: List[str]) -> Dict[str, str]:
    """Return only the specified keys from an env file."""
    if not env_file.exists():
        raise FilterError(f"env file not found: {env_file}")
    data = _parse_env(env_file)
    missing = [k for k in keys if k not in data]
    if missing:
        raise FilterError(f"keys not found in env file: {missing}")
    return {k: data[k] for k in keys}


def filter_by_pattern(env_file: Path, pattern: str) -> Dict[str, str]:
    """Return keys matching a glob pattern from an env file."""
    if not env_file.exists():
        raise FilterError(f"env file not found: {env_file}")
    try:
        re.compile(fnmatch.translate(pattern))
    except re.error as exc:
        raise FilterError(f"invalid pattern: {pattern}") from exc
    data = _parse_env(env_file)
    return {k: v for k, v in data.items() if fnmatch.fnmatch(k, pattern)}


def exclude_keys(env_file: Path, keys: List[str]) -> Dict[str, str]:
    """Return all keys except the specified ones."""
    if not env_file.exists():
        raise FilterError(f"env file not found: {env_file}")
    data = _parse_env(env_file)
    return {k: v for k, v in data.items() if k not in keys}
