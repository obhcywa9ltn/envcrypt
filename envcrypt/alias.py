"""Alias management for vault file nicknames."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class AliasError(Exception):
    pass


def get_aliases_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".envcrypt" / "aliases.json"


def load_aliases(base_dir: Path | None = None) -> Dict[str, str]:
    path = get_aliases_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AliasError(f"Invalid aliases file: {exc}") from exc
    if not isinstance(data, dict):
        raise AliasError("Aliases file must be a JSON object")
    return data


def save_aliases(aliases: Dict[str, str], base_dir: Path | None = None) -> None:
    path = get_aliases_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aliases, indent=2))


def add_alias(name: str, target: str, base_dir: Path | None = None) -> Dict[str, str]:
    aliases = load_aliases(base_dir)
    if name in aliases:
        raise AliasError(f"Alias '{name}' already exists")
    aliases[name] = target
    save_aliases(aliases, base_dir)
    return aliases


def remove_alias(name: str, base_dir: Path | None = None) -> Dict[str, str]:
    aliases = load_aliases(base_dir)
    if name not in aliases:
        raise AliasError(f"Alias '{name}' not found")
    del aliases[name]
    save_aliases(aliases, base_dir)
    return aliases


def resolve_alias(name: str, base_dir: Path | None = None) -> str:
    aliases = load_aliases(base_dir)
    if name not in aliases:
        raise AliasError(f"Alias '{name}' not found")
    return aliases[name]
