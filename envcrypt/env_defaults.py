"""Manage default values for .env keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class DefaultsError(Exception):
    """Raised when a defaults operation fails."""


def get_defaults_path(base_dir: Optional[Path] = None) -> Path:
    root = base_dir if base_dir is not None else Path.cwd()
    return root / ".envcrypt" / "defaults.json"


def load_defaults(base_dir: Optional[Path] = None) -> Dict[str, str]:
    path = get_defaults_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise DefaultsError(f"Invalid JSON in defaults file: {exc}") from exc
    if not isinstance(data, dict):
        raise DefaultsError("Defaults file must contain a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def save_defaults(defaults: Dict[str, str], base_dir: Optional[Path] = None) -> None:
    path = get_defaults_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(defaults, indent=2))


def set_default(key: str, value: str, base_dir: Optional[Path] = None) -> Dict[str, str]:
    defaults = load_defaults(base_dir)
    defaults[key] = value
    save_defaults(defaults, base_dir)
    return defaults


def remove_default(key: str, base_dir: Optional[Path] = None) -> Dict[str, str]:
    defaults = load_defaults(base_dir)
    if key not in defaults:
        raise DefaultsError(f"Key '{key}' not found in defaults")
    del defaults[key]
    save_defaults(defaults, base_dir)
    return defaults


def apply_defaults(env_path: Path, base_dir: Optional[Path] = None) -> Dict[str, str]:
    """Fill in missing keys in an env file from defaults. Returns applied mapping."""
    if not env_path.exists():
        raise DefaultsError(f"Env file not found: {env_path}")
    defaults = load_defaults(base_dir)
    if not defaults:
        return {}
    existing_keys: set[str] = set()
    lines = env_path.read_text().splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            continue
        existing_keys.add(stripped.split("=", 1)[0].strip())
    applied: Dict[str, str] = {}
    additions: list[str] = []
    for key, value in defaults.items():
        if key not in existing_keys:
            additions.append(f"{key}={value}")
            applied[key] = value
    if additions:
        text = env_path.read_text()
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n".join(additions) + "\n"
        env_path.write_text(text)
    return applied
