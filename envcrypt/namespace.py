"""Namespace support for grouping env files under logical names."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class NamespaceError(Exception):
    pass


def get_namespaces_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".envcrypt" / "namespaces.json"


def load_namespaces(base_dir: Path | None = None) -> Dict[str, List[str]]:
    path = get_namespaces_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise NamespaceError(f"Invalid namespaces file: {exc}") from exc
    if not isinstance(data, dict):
        raise NamespaceError("Namespaces file must be a JSON object")
    return data


def save_namespaces(namespaces: Dict[str, List[str]], base_dir: Path | None = None) -> None:
    path = get_namespaces_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(namespaces, indent=2))


def add_to_namespace(namespace: str, env_file: str, base_dir: Path | None = None) -> Dict[str, List[str]]:
    namespaces = load_namespaces(base_dir)
    files = namespaces.setdefault(namespace, [])
    if env_file in files:
        raise NamespaceError(f"{env_file!r} already in namespace {namespace!r}")
    files.append(env_file)
    save_namespaces(namespaces, base_dir)
    return namespaces


def remove_from_namespace(namespace: str, env_file: str, base_dir: Path | None = None) -> Dict[str, List[str]]:
    namespaces = load_namespaces(base_dir)
    if namespace not in namespaces or env_file not in namespaces[namespace]:
        raise NamespaceError(f"{env_file!r} not found in namespace {namespace!r}")
    namespaces[namespace].remove(env_file)
    if not namespaces[namespace]:
        del namespaces[namespace]
    save_namespaces(namespaces, base_dir)
    return namespaces


def list_namespaces(base_dir: Path | None = None) -> Dict[str, List[str]]:
    return load_namespaces(base_dir)
