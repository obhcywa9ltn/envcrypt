"""Merge two .env files, with conflict detection and resolution strategies."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional


class MergeError(Exception):
    pass


class ConflictStrategy(str, Enum):
    OURS = "ours"
    THEIRS = "theirs"
    ERROR = "error"


class MergeConflict(NamedTuple):
    key: str
    ours: str
    theirs: str


class MergeResult(NamedTuple):
    merged: Dict[str, str]
    conflicts: List[MergeConflict]


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


def merge_env_files(
    ours: Path,
    theirs: Path,
    dest: Optional[Path] = None,
    strategy: ConflictStrategy = ConflictStrategy.ERROR,
) -> MergeResult:
    """Merge two env files into dest (or ours if dest is None)."""
    if not ours.exists():
        raise MergeError(f"Base file not found: {ours}")
    if not theirs.exists():
        raise MergeError(f"Incoming file not found: {theirs}")

    base = _parse_env(ours)
    incoming = _parse_env(theirs)

    merged: Dict[str, str] = dict(base)
    conflicts: List[MergeConflict] = []

    for key, value in incoming.items():
        if key not in merged:
            merged[key] = value
        elif merged[key] != value:
            conflict = MergeConflict(key=key, ours=merged[key], theirs=value)
            conflicts.append(conflict)
            if strategy == ConflictStrategy.THEIRS:
                merged[key] = value
            elif strategy == ConflictStrategy.ERROR:
                raise MergeError(
                    f"Conflict on key '{key}': ours={merged[key]!r} theirs={value!r}"
                )
            # OURS: keep existing value

    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{k}={v}" for k, v in merged.items()]
        dest.write_text("\n".join(lines) + "\n")

    return MergeResult(merged=merged, conflicts=conflicts)
