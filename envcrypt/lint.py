"""Lint .env files for common issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class LintError(Exception):
    pass


@dataclass
class LintIssue:
    line: int
    message: str


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


def lint_env_file(env_path: Path) -> LintResult:
    """Lint an .env file and return a LintResult with any issues found."""
    if not env_path.exists():
        raise LintError(f"File not found: {env_path}")

    result = LintResult(path=env_path)
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(env_path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            result.issues.append(LintIssue(lineno, f"Missing '=' separator: {raw!r}"))
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            result.issues.append(LintIssue(lineno, "Empty key"))
            continue
        if " " in key:
            result.issues.append(LintIssue(lineno, f"Key contains whitespace: {key!r}"))
        if key in seen_keys:
            result.issues.append(
                LintIssue(lineno, f"Duplicate key {key!r} (first seen on line {seen_keys[key]})")
            )
        else:
            seen_keys[key] = lineno
        if value.startswith(("'", '"')) and not (
            value.endswith(value[0]) and len(value) > 1
        ):
            result.issues.append(LintIssue(lineno, f"Unclosed quote for key {key!r}"))

    return result
