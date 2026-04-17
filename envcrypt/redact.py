"""Redaction utilities for masking sensitive .env values in output."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(password|secret|token|key|api_key|private|auth|credential)"),
]

REDACT_PLACEHOLDER = "***REDACTED***"


class RedactError(Exception):
    pass


def is_sensitive(key: str) -> bool:
    """Return True if the key name looks sensitive."""
    return any(p.search(key) for p in SENSITIVE_PATTERNS)


def redact_dict(env: Dict[str, str], keys: List[str] | None = None) -> Dict[str, str]:
    """Return a copy of env with sensitive (or specified) values redacted."""
    result = {}
    for k, v in env.items():
        if (keys and k in keys) or (not keys and is_sensitive(k)):
            result[k] = REDACT_PLACEHOLDER
        else:
            result[k] = v
    return result


def redact_file(src: Path, dest: Path, keys: List[str] | None = None) -> int:
    """Write a redacted copy of an .env file to dest. Returns number of redacted lines."""
    if not src.exists():
        raise RedactError(f"Source file not found: {src}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    redacted_count = 0
    lines_out: List[str] = []

    for line in src.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            lines_out.append(line)
            continue
        k, _, v = stripped.partition("=")
        k = k.strip()
        if (keys and k in keys) or (not keys and is_sensitive(k)):
            lines_out.append(f"{k}={REDACT_PLACEHOLDER}")
            redacted_count += 1
        else:
            lines_out.append(line)

    dest.write_text("\n".join(lines_out) + "\n")
    return redacted_count
