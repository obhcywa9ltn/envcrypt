"""Vault file history tracking for envcrypt."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class HistoryError(Exception):
    pass


def get_history_path(base_dir: str | Path | None = None) -> Path:
    base = Path(base_dir) if base_dir else Path.cwd()
    return base / ".envcrypt" / "history.json"


def load_history(base_dir: str | Path | None = None) -> list[dict[str, Any]]:
    path = get_history_path(base_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise HistoryError(f"Invalid history file: {exc}") from exc
    if not isinstance(data, list):
        raise HistoryError("History file root must be a list")
    return data


def save_history(entries: list[dict[str, Any]], base_dir: str | Path | None = None) -> None:
    path = get_history_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_event(
    action: str,
    env_file: str,
    actor: str = "unknown",
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    entries = load_history(base_dir)
    entry: dict[str, Any] = {
        "action": action,
        "env_file": env_file,
        "actor": actor,
        "timestamp": time.time(),
    }
    entries.append(entry)
    save_history(entries, base_dir)
    return entry


def clear_history(base_dir: str | Path | None = None) -> None:
    save_history([], base_dir)
