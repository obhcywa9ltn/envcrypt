"""Variable interpolation for .env files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional


class InterpolateError(Exception):
    """Raised when interpolation fails."""


_VAR_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


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


def interpolate_value(value: str, context: Dict[str, str]) -> str:
    """Expand ${VAR} and $VAR references using *context*."""

    def _replace(match: re.Match) -> str:
        name = match.group(1) or match.group(2)
        if name not in context:
            raise InterpolateError(f"Undefined variable: {name!r}")
        return context[name]

    return _VAR_RE.sub(_replace, value)


def interpolate_env_file(
    src: Path,
    dest: Optional[Path] = None,
    *,
    extra_context: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Interpolate all values in *src* and write result to *dest*.

    Returns the fully-resolved key/value mapping.
    """
    if not src.exists():
        raise InterpolateError(f"Source file not found: {src}")

    pairs = _parse_env(src)
    context: Dict[str, str] = {**(extra_context or {}), **pairs}

    resolved: Dict[str, str] = {}
    for key, raw_value in pairs.items():
        try:
            resolved[key] = interpolate_value(raw_value, context)
        except InterpolateError as exc:
            raise InterpolateError(f"Error interpolating {key!r}: {exc}") from exc

    if dest is None:
        dest = src.with_suffix(".interpolated" + src.suffix)

    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in resolved.items()]
    dest.write_text("\n".join(lines) + "\n")

    return resolved


def list_references(src: Path) -> Dict[str, list]:
    """Return a mapping of key -> list of variable names it references."""
    if not src.exists():
        raise InterpolateError(f"Source file not found: {src}")

    pairs = _parse_env(src)
    return {
        key: [m.group(1) or m.group(2) for m in _VAR_RE.finditer(value)]
        for key, value in pairs.items()
    }
