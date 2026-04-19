"""Group env keys into named sections."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List


class GroupError(Exception):
    pass


def get_groups_path(base_dir: str | None = None) -> Path:
    base = Path(base_dir) if base_dir else Path.cwd()
    return base / ".envcrypt" / "groups.json"


def load_groups(base_dir: str | None = None) -> Dict[str, List[str]]:
    path = get_groups_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise GroupError(f"Invalid JSON in groups file: {exc}") from exc
    if not isinstance(data, dict):
        raise GroupError("Groups file root must be a JSON object")
    return data


def save_groups(groups: Dict[str, List[str]], base_dir: str | None = None) -> None:
    path = get_groups_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(groups, indent=2))


def add_to_group(group: str, key: str, base_dir: str | None = None) -> Dict[str, List[str]]:
    groups = load_groups(base_dir)
    members = groups.setdefault(group, [])
    if key in members:
        raise GroupError(f"Key '{key}' already in group '{group}'")
    members.append(key)
    save_groups(groups, base_dir)
    return groups


def remove_from_group(group: str, key: str, base_dir: str | None = None) -> Dict[str, List[str]]:
    groups = load_groups(base_dir)
    if group not in groups:
        raise GroupError(f"Group '{group}' not found")
    if key not in groups[group]:
        raise GroupError(f"Key '{key}' not in group '{group}'")
    groups[group].remove(key)
    if not groups[group]:
        del groups[group]
    save_groups(groups, base_dir)
    return groups


def list_groups(base_dir: str | None = None) -> Dict[str, List[str]]:
    return load_groups(base_dir)
