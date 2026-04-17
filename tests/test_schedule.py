"""Tests for envcrypt.schedule."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from envcrypt.schedule import (
    ScheduleError,
    get_schedule_path,
    load_schedule,
    save_schedule,
    add_schedule,
    remove_schedule,
    update_last_run,
    due_schedules,
    ScheduleEntry,
)


def test_get_schedule_path_defaults_to_cwd():
    p = get_schedule_path()
    assert p == Path.cwd() / ".envcrypt_schedule.json"


def test_get_schedule_path_uses_base_dir(tmp_path):
    p = get_schedule_path(tmp_path)
    assert p == tmp_path / ".envcrypt_schedule.json"


def test_load_schedule_returns_empty_when_missing(tmp_path):
    assert load_schedule(tmp_path) == {}


def test_load_schedule_parses_valid_file(tmp_path):
    data = {"rotate": {"name": "rotate", "interval_days": 30, "last_run": None}}
    (tmp_path / ".envcrypt_schedule.json").write_text(json.dumps(data))
    entries = load_schedule(tmp_path)
    assert "rotate" in entries
    assert entries["rotate"].interval_days == 30


def test_load_schedule_raises_on_invalid_json(tmp_path):
    (tmp_path / ".envcrypt_schedule.json").write_text("not json")
    with pytest.raises(ScheduleError, match="Invalid schedule file"):
        load_schedule(tmp_path)


def test_load_schedule_raises_when_root_not_dict(tmp_path):
    (tmp_path / ".envcrypt_schedule.json").write_text("[]")
    with pytest.raises(ScheduleError, match="JSON object"):
        load_schedule(tmp_path)


def test_add_schedule_creates_entry(tmp_path):
    entry = add_schedule("sync", 7, tmp_path)
    assert entry.name == "sync"
    assert entry.interval_days == 7
    assert entry.last_run is None
    entries = load_schedule(tmp_path)
    assert "sync" in entries


def test_add_schedule_raises_on_duplicate(tmp_path):
    add_schedule("sync", 7, tmp_path)
    with pytest.raises(ScheduleError, match="already exists"):
        add_schedule("sync", 14, tmp_path)


def test_remove_schedule_deletes_entry(tmp_path):
    add_schedule("sync", 7, tmp_path)
    remove_schedule("sync", tmp_path)
    assert "sync" not in load_schedule(tmp_path)


def test_remove_schedule_raises_when_missing(tmp_path):
    with pytest.raises(ScheduleError, match="not found"):
        remove_schedule("ghost", tmp_path)


def test_update_last_run_sets_date(tmp_path):
    add_schedule("rotate", 30, tmp_path)
    today = date.today().isoformat()
    update_last_run("rotate", today, tmp_path)
    entries = load_schedule(tmp_path)
    assert entries["rotate"].last_run == today


def test_due_schedules_includes_never_run(tmp_path):
    add_schedule("rotate", 30, tmp_path)
    due = due_schedules(tmp_path)
    assert any(e.name == "rotate" for e in due)


def test_due_schedules_excludes_recent(tmp_path):
    add_schedule("rotate", 30, tmp_path)
    today = date.today().isoformat()
    update_last_run("rotate", today, tmp_path)
    due = due_schedules(tmp_path)
    assert not any(e.name == "rotate" for e in due)


def test_due_schedules_includes_overdue(tmp_path):
    add_schedule("rotate", 7, tmp_path)
    old = (date.today() - timedelta(days=10)).isoformat()
    update_last_run("rotate", old, tmp_path)
    due = due_schedules(tmp_path)
    assert any(e.name == "rotate" for e in due)
