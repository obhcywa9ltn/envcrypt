"""Count and summarize key occurrences across multiple .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class CountError(Exception):
    """Raised when env counting fails."""


@dataclass
class KeyCount:
    key: str
    occurrences: int
    files: List[str] = field(default_factory=list)


@dataclass
class CountResult:
    total_files: int
    total_keys: int
    unique_keys: int
    counts: Dict[str, KeyCount] = field(default_factory=dict)


def _parse_env(path: Path) -> List[str]:
    keys: List[str] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            keys.append(stripped.split("=", 1)[0].strip())
    return keys


def count_keys(env_files: List[Path]) -> CountResult:
    """Count key occurrences across multiple .env files."""
    if not env_files:
        raise CountError("No env files provided")

    missing = [str(p) for p in env_files if not p.exists()]
    if missing:
        raise CountError(f"Files not found: {', '.join(missing)}")

    counts: Dict[str, KeyCount] = {}
    total_keys = 0

    for path in env_files:
        keys = _parse_env(path)
        total_keys += len(keys)
        for key in keys:
            if key not in counts:
                counts[key] = KeyCount(key=key, occurrences=0)
            counts[key].occurrences += 1
            counts[key].files.append(str(path))

    return CountResult(
        total_files=len(env_files),
        total_keys=total_keys,
        unique_keys=len(counts),
        counts=counts,
    )


def keys_in_all(result: CountResult) -> List[str]:
    """Return keys that appear in every file."""
    return [
        key
        for key, kc in result.counts.items()
        if kc.occurrences == result.total_files
    ]


def keys_in_one(result: CountResult) -> List[str]:
    """Return keys that appear in exactly one file."""
    return [key for key, kc in result.counts.items() if kc.occurrences == 1]
