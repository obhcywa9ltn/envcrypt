"""Scheduled rotation and sync reminders for envcrypt."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

SCHEDULE_FILE = ".envcrypt_schedule.json"


class ScheduleError(Exception):
    pass


@dataclass
class ScheduleEntry:
    name: str
    interval_days: int
    last_run: Optional[str] = None  # ISO date string


def get_schedule_path(base_dir: Optional[Path] = None) -> Path:
    base = base_dir or Path.cwd()
    return base / SCHEDULE_FILE


def load_schedule(base_dir: Optional[Path] = None) -> dict[str, ScheduleEntry]:
    path = get_schedule_path(base_dir)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ScheduleError(f"Invalid schedule file: {exc}") from exc
    if not isinstance(raw, dict):
        raise ScheduleError("Schedule file must be a JSON object")
    return {k: ScheduleEntry(**v) for k, v in raw.items()}


def save_schedule(entries: dict[str, ScheduleEntry], base_dir: Optional[Path] = None) -> None:
    path = get_schedule_path(base_dir)
    path.write_text(json.dumps({k: asdict(v) for k, v in entries.items()}, indent=2))


def add_schedule(name: str, interval_days: int, base_dir: Optional[Path] = None) -> ScheduleEntry:
    entries = load_schedule(base_dir)
    if name in entries:
        raise ScheduleError(f"Schedule '{name}' already exists")
    entry = ScheduleEntry(name=name, interval_days=interval_days)
    entries[name] = entry
    save_schedule(entries, base_dir)
    return entry


def remove_schedule(name: str, base_dir: Optional[Path] = None) -> None:
    entries = load_schedule(base_dir)
    if name not in entries:
        raise ScheduleError(f"Schedule '{name}' not found")
    del entries[name]
    save_schedule(entries, base_dir)


def update_last_run(name: str, date_str: str, base_dir: Optional[Path] = None) -> None:
    entries = load_schedule(base_dir)
    if name not in entries:
        raise ScheduleError(f"Schedule '{name}' not found")
    entries[name].last_run = date_str
    save_schedule(entries, base_dir)


def due_schedules(base_dir: Optional[Path] = None) -> list[ScheduleEntry]:
    from datetime import date, timedelta
    entries = load_schedule(base_dir)
    today = date.today()
    due = []
    for entry in entries.values():
        if entry.last_run is None:
            due.append(entry)
        else:
            last = date.fromisoformat(entry.last_run)
            if today >= last + timedelta(days=entry.interval_days):
                due.append(entry)
    return due
