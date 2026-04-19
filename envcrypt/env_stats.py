"""Statistics and summary for .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class StatsError(Exception):
    pass


@dataclass
class EnvStats:
    total_lines: int
    blank_lines: int
    comment_lines: int
    key_count: int
    empty_values: int
    duplicate_keys: list[str]

    @property
    def defined_keys(self) -> int:
        return self.key_count - self.empty_values


def _parse_lines(lines: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs.append((key.strip(), value.strip()))
    return pairs


def env_stats(path: Path) -> EnvStats:
    """Return statistics for the given .env file."""
    if not path.exists():
        raise StatsError(f"File not found: {path}")

    lines = path.read_text().splitlines()
    blank = sum(1 for l in lines if not l.strip())
    comments = sum(1 for l in lines if l.strip().startswith("#"))
    pairs = _parse_lines(lines)
    empty_values = sum(1 for _, v in pairs if v == "")

    seen: dict[str, int] = {}
    for key, _ in pairs:
        seen[key] = seen.get(key, 0) + 1
    duplicates = [k for k, count in seen.items() if count > 1]

    return EnvStats(
        total_lines=len(lines),
        blank_lines=blank,
        comment_lines=comments,
        key_count=len(pairs),
        empty_values=empty_values,
        duplicate_keys=duplicates,
    )


def summary_text(stats: EnvStats) -> str:
    """Return a human-readable summary string."""
    lines = [
        f"Total lines   : {stats.total_lines}",
        f"Keys defined  : {stats.key_count}",
        f"  with values : {stats.defined_keys}",
        f"  empty       : {stats.empty_values}",
        f"Blank lines   : {stats.blank_lines}",
        f"Comments      : {stats.comment_lines}",
    ]
    if stats.duplicate_keys:
        lines.append(f"Duplicates    : {', '.join(stats.duplicate_keys)}")
    else:
        lines.append("Duplicates    : none")
    return "\n".join(lines)
