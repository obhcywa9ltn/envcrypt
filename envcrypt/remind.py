"""Rotation reminders: track when keys were last rotated and warn if overdue."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DEFAULT_FILENAME = ".envcrypt-remind.json"
DEFAULT_INTERVAL_DAYS = 30


class RemindError(Exception):
    pass


def get_remind_path(base_dir: Optional[Path] = None) -> Path:
    base = base_dir or Path.cwd()
    return base / DEFAULT_FILENAME


def load_remind(base_dir: Optional[Path] = None) -> dict:
    path = get_remind_path(base_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise RemindError(f"Invalid remind file: {exc}") from exc


def save_remind(data: dict, base_dir: Optional[Path] = None) -> None:
    path = get_remind_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def record_rotation(name: str, base_dir: Optional[Path] = None) -> str:
    data = load_remind(base_dir)
    ts = datetime.utcnow().isoformat()
    data[name] = {"last_rotated": ts}
    save_remind(data, base_dir)
    return ts


def check_due(
    name: str,
    interval_days: int = DEFAULT_INTERVAL_DAYS,
    base_dir: Optional[Path] = None,
) -> bool:
    """Return True if rotation is due (or never recorded)."""
    data = load_remind(base_dir)
    entry = data.get(name)
    if not entry:
        return True
    try:
        last = datetime.fromisoformat(entry["last_rotated"])
    except (KeyError, ValueError) as exc:
        raise RemindError(f"Corrupt remind entry for '{name}': {exc}") from exc
    return datetime.utcnow() - last >= timedelta(days=interval_days)


def list_remind(base_dir: Optional[Path] = None) -> dict:
    return load_remind(base_dir)
