"""Diff statistics between two .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class DiffStatError(Exception):
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


@dataclass
class DiffStat:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    @property
    def is_clean(self) -> bool:
        return self.total_changes == 0


def diff_stat(base: Path, incoming: Path) -> DiffStat:
    """Return a DiffStat comparing base env to incoming env."""
    if not base.exists():
        raise DiffStatError(f"Base file not found: {base}")
    if not incoming.exists():
        raise DiffStatError(f"Incoming file not found: {incoming}")

    base_env = _parse_env(base)
    incoming_env = _parse_env(incoming)

    stat = DiffStat()
    all_keys = set(base_env) | set(incoming_env)

    for key in sorted(all_keys):
        in_base = key in base_env
        in_incoming = key in incoming_env
        if in_base and in_incoming:
            if base_env[key] == incoming_env[key]:
                stat.unchanged.append(key)
            else:
                stat.changed.append(key)
        elif in_incoming:
            stat.added.append(key)
        else:
            stat.removed.append(key)

    return stat
