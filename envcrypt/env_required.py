"""Check and enforce required keys in .env files."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class RequiredError(Exception):
    """Raised when a required-keys operation fails."""


@dataclass
class MissingKeyResult:
    missing: List[str] = field(default_factory=list)
    present: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0


def get_required_path(base_dir: Optional[str] = None) -> Path:
    base = Path(base_dir) if base_dir else Path.cwd()
    return base / ".envcrypt" / "required.json"


def load_required(base_dir: Optional[str] = None) -> List[str]:
    path = get_required_path(base_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RequiredError(f"Invalid JSON in required file: {exc}") from exc
    if not isinstance(data, list):
        raise RequiredError("Required file must contain a JSON array")
    return [str(k) for k in data]


def save_required(keys: List[str], base_dir: Optional[str] = None) -> None:
    path = get_required_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(set(keys)), indent=2))


def add_required_key(key: str, base_dir: Optional[str] = None) -> List[str]:
    keys = load_required(base_dir)
    if key in keys:
        return keys
    keys.append(key)
    save_required(keys, base_dir)
    return sorted(set(keys))


def remove_required_key(key: str, base_dir: Optional[str] = None) -> List[str]:
    keys = load_required(base_dir)
    if key not in keys:
        raise RequiredError(f"Key '{key}' is not in the required list")
    keys = [k for k in keys if k != key]
    save_required(keys, base_dir)
    return keys


def _parse_env(path: Path) -> dict:
    result = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            k, _, v = stripped.partition("=")
            result[k.strip()] = v.strip()
    return result


def check_required(env_file: str, base_dir: Optional[str] = None) -> MissingKeyResult:
    path = Path(env_file)
    if not path.exists():
        raise RequiredError(f"Env file not found: {env_file}")
    keys = load_required(base_dir)
    env = _parse_env(path)
    missing = [k for k in keys if k not in env]
    present = [k for k in keys if k in env]
    return MissingKeyResult(missing=missing, present=present)
