"""Access control: restrict which recipients can decrypt which env files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class AccessError(Exception):
    pass


def get_access_path(base_dir: str | None = None) -> Path:
    base = Path(base_dir) if base_dir else Path.cwd()
    return base / ".envcrypt" / "access.json"


def load_access(base_dir: str | None = None) -> Dict[str, List[str]]:
    path = get_access_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AccessError(f"Invalid JSON in access file: {exc}") from exc
    if not isinstance(data, dict):
        raise AccessError("Access file root must be a JSON object")
    return data


def save_access(mapping: Dict[str, List[str]], base_dir: str | None = None) -> None:
    path = get_access_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2))


def grant_access(env_name: str, recipient: str, base_dir: str | None = None) -> Dict[str, List[str]]:
    mapping = load_access(base_dir)
    allowed = mapping.setdefault(env_name, [])
    if recipient not in allowed:
        allowed.append(recipient)
    save_access(mapping, base_dir)
    return mapping


def revoke_access(env_name: str, recipient: str, base_dir: str | None = None) -> Dict[str, List[str]]:
    mapping = load_access(base_dir)
    allowed = mapping.get(env_name, [])
    if recipient not in allowed:
        raise AccessError(f"Recipient '{recipient}' not in access list for '{env_name}'")
    allowed.remove(recipient)
    mapping[env_name] = allowed
    save_access(mapping, base_dir)
    return mapping


def is_allowed(env_name: str, recipient: str, base_dir: str | None = None) -> bool:
    mapping = load_access(base_dir)
    allowed = mapping.get(env_name)
    if allowed is None:
        return True  # no restrictions defined
    return recipient in allowed
