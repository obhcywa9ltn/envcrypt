"""Validate .env files against a set of rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class ValidateError(Exception):
    pass


@dataclass
class ValidationIssue:
    line_number: int
    key: str
    message: str


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


def _parse_env(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (lineno, key, value) for non-comment, non-blank lines."""
    results = []
    for i, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            results.append((i, line, ''))
        else:
            k, _, v = line.partition('=')
            results.append((i, k.strip(), v.strip()))
    return results


def validate_env_file(
    env_file: Path,
    *,
    require_values: bool = False,
    require_uppercase: bool = True,
    required_keys: list[str] | None = None,
) -> ValidationResult:
    """Validate an .env file and return a ValidationResult."""
    if not env_file.exists():
        raise ValidateError(f"env file not found: {env_file}")

    result = ValidationResult()
    entries = _parse_env(env_file)
    found_keys = set()

    for lineno, key, value in entries:
        if '=' not in key and not value:
            result.issues.append(ValidationIssue(lineno, key, "missing '=' separator"))
            continue
        found_keys.add(key)
        if require_uppercase and not _KEY_RE.match(key):
            result.issues.append(ValidationIssue(lineno, key, f"key '{key}' must match [A-Z_][A-Z0-9_]*"))
        if require_values and not value:
            result.issues.append(ValidationIssue(lineno, key, f"key '{key}' has no value"))

    for req in (required_keys or []):
        if req not in found_keys:
            result.issues.append(ValidationIssue(0, req, f"required key '{req}' is missing"))

    return result
