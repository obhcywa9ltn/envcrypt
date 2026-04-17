"""Inline comment management for .env files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class CommentError(Exception):
    pass


def get_comments_path(base_dir: str | None = None) -> Path:
    base = Path(base_dir) if base_dir else Path.cwd()
    return base / ".envcrypt" / "comments.json"


def load_comments(base_dir: str | None = None) -> Dict[str, str]:
    path = get_comments_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise CommentError(f"Invalid comments file: {exc}") from exc
    if not isinstance(data, dict):
        raise CommentError("Comments file must be a JSON object")
    return data


def save_comments(comments: Dict[str, str], base_dir: str | None = None) -> None:
    path = get_comments_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(comments, indent=2))


def add_comment(key: str, comment: str, base_dir: str | None = None) -> Dict[str, str]:
    if not key:
        raise CommentError("Key must not be empty")
    comments = load_comments(base_dir)
    comments[key] = comment
    save_comments(comments, base_dir)
    return comments


def remove_comment(key: str, base_dir: str | None = None) -> Dict[str, str]:
    comments = load_comments(base_dir)
    if key not in comments:
        raise CommentError(f"No comment for key: {key}")
    del comments[key]
    save_comments(comments, base_dir)
    return comments


def get_comment(key: str, base_dir: str | None = None) -> str | None:
    return load_comments(base_dir).get(key)
