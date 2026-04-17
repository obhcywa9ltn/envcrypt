"""Tests for envcrypt.remind."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from envcrypt.remind import (
    RemindError,
    check_due,
    get_remind_path,
    list_remind,
    load_remind,
    record_rotation,
    save_remind,
)


def test_get_remind_path_defaults_to_cwd():
    p = get_remind_path()
    assert p == Path.cwd() / ".envcrypt-remind.json"


def test_get_remind_path_uses_base_dir(tmp_path):
    assert get_remind_path(tmp_path) == tmp_path / ".envcrypt-remind.json"


def test_load_remind_returns_empty_when_missing(tmp_path):
    assert load_remind(tmp_path) == {}


def test_load_remind_parses_valid_file(tmp_path):
    data = {"key": {"last_rotated": "2024-01-01T00:00:00"}}
    (tmp_path / ".envcrypt-remind.json").write_text(json.dumps(data))
    assert load_remind(tmp_path) == data


def test_load_remind_raises_on_invalid_json(tmp_path):
    (tmp_path / ".envcrypt-remind.json").write_text("not json")
    with pytest.raises(RemindError):
        load_remind(tmp_path)


def test_save_remind_writes_file(tmp_path):
    save_remind({"k": {"last_rotated": "2024-01-01T00:00:00"}}, tmp_path)
    raw = json.loads((tmp_path / ".envcrypt-remind.json").read_text())
    assert "k" in raw


def test_record_rotation_stores_timestamp(tmp_path):
    ts = record_rotation("mykey", tmp_path)
    data = load_remind(tmp_path)
    assert data["mykey"]["last_rotated"] == ts


def test_check_due_returns_true_when_never_recorded(tmp_path):
    assert check_due("ghost", base_dir=tmp_path) is True


def test_check_due_returns_false_when_recently_rotated(tmp_path):
    record_rotation("fresh", tmp_path)
    assert check_due("fresh", interval_days=30, base_dir=tmp_path) is False


def test_check_due_returns_true_when_overdue(tmp_path):
    old_ts = (datetime.utcnow() - timedelta(days=40)).isoformat()
    save_remind({"old": {"last_rotated": old_ts}}, tmp_path)
    assert check_due("old", interval_days=30, base_dir=tmp_path) is True


def test_check_due_raises_on_corrupt_entry(tmp_path):
    save_remind({"bad": {"last_rotated": "not-a-date"}}, tmp_path)
    with pytest.raises(RemindError):
        check_due("bad", base_dir=tmp_path)


def test_list_remind_returns_all_entries(tmp_path):
    record_rotation("a", tmp_path)
    record_rotation("b", tmp_path)
    result = list_remind(tmp_path)
    assert set(result.keys()) == {"a", "b"}
