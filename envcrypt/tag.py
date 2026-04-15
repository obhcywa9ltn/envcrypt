"""Tag management for labelling encrypted env files with metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

TAGS_FILENAME = ".envcrypt_tags.json"


class TagError(Exception):
    """Raised when a tag operation fails."""


def get_tags_path(base_dir: Path | None = None) -> Path:
    """Return the path to the tags file."""
    root = base_dir if base_dir is not None else Path.cwd()
    return root / TAGS_FILENAME


def load_tags(base_dir: Path | None = None) -> Dict[str, List[str]]:
    """Load tags from disk. Returns empty dict if file is missing."""
    path = get_tags_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TagError(f"Invalid JSON in tags file: {exc}") from exc
    if not isinstance(data, dict):
        raise TagError("Tags file root must be a JSON object")
    for key, value in data.items():
        if not isinstance(value, list):
            raise TagError(f"Tags for '{key}' must be a list")
    return data


def save_tags(tags: Dict[str, List[str]], base_dir: Path | None = None) -> None:
    """Persist tags to disk."""
    path = get_tags_path(base_dir)
    path.write_text(json.dumps(tags, indent=2))


def add_tag(file_key: str, tag: str, base_dir: Path | None = None) -> Dict[str, List[str]]:
    """Add *tag* to *file_key*. No-op if already present."""
    tags = load_tags(base_dir)
    existing = tags.setdefault(file_key, [])
    if tag not in existing:
        existing.append(tag)
    save_tags(tags, base_dir)
    return tags


def remove_tag(file_key: str, tag: str, base_dir: Path | None = None) -> Dict[str, List[str]]:
    """Remove *tag* from *file_key*. Raises TagError if not present."""
    tags = load_tags(base_dir)
    if file_key not in tags or tag not in tags[file_key]:
        raise TagError(f"Tag '{tag}' not found on '{file_key}'")
    tags[file_key].remove(tag)
    if not tags[file_key]:
        del tags[file_key]
    save_tags(tags, base_dir)
    return tags


def list_tags(file_key: str, base_dir: Path | None = None) -> List[str]:
    """Return tags for *file_key*, or empty list if none."""
    return load_tags(base_dir).get(file_key, [])
