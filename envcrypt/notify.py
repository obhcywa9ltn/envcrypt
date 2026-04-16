"""Notification helpers for envcrypt events."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any


class NotifyError(Exception):
    pass


def get_notify_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".envcrypt" / "notifications.json"


def load_notifications(base_dir: Path | None = None) -> List[Dict[str, Any]]:
    path = get_notify_path(base_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise NotifyError(f"Invalid notifications file: {exc}") from exc
    if not isinstance(data, list):
        raise NotifyError("Notifications file must contain a JSON array")
    return data


def save_notifications(entries: List[Dict[str, Any]], base_dir: Path | None = None) -> None:
    path = get_notify_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def push_notification(
    event: str,
    detail: str,
    base_dir: Path | None = None,
) -> Dict[str, Any]:
    entries = load_notifications(base_dir)
    entry: Dict[str, Any] = {"event": event, "detail": detail}
    entries.append(entry)
    save_notifications(entries, base_dir)
    return entry


def clear_notifications(base_dir: Path | None = None) -> int:
    entries = load_notifications(base_dir)
    count = len(entries)
    save_notifications([], base_dir)
    return count


def list_notifications(base_dir: Path | None = None) -> List[Dict[str, Any]]:
    return load_notifications(base_dir)
