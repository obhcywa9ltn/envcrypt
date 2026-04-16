"""Tests for envcrypt.notify."""
import json
import pytest
from pathlib import Path
from envcrypt.notify import (
    NotifyError,
    get_notify_path,
    load_notifications,
    save_notifications,
    push_notification,
    clear_notifications,
    list_notifications,
)


def test_get_notify_path_defaults_to_cwd():
    path = get_notify_path()
    assert path == Path.cwd() / ".envcrypt" / "notifications.json"


def test_get_notify_path_uses_base_dir(tmp_path):
    path = get_notify_path(tmp_path)
    assert path == tmp_path / ".envcrypt" / "notifications.json"


def test_load_notifications_returns_empty_when_missing(tmp_path):
    assert load_notifications(tmp_path) == []


def test_load_notifications_parses_valid_file(tmp_path):
    data = [{"event": "lock", "detail": "dev.env"}]
    p = tmp_path / ".envcrypt" / "notifications.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(data))
    assert load_notifications(tmp_path) == data


def test_load_notifications_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "notifications.json"
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(NotifyError, match="Invalid"):
        load_notifications(tmp_path)


def test_load_notifications_raises_when_root_not_list(tmp_path):
    p = tmp_path / ".envcrypt" / "notifications.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"key": "value"}))
    with pytest.raises(NotifyError, match="array"):
        load_notifications(tmp_path)


def test_push_notification_appends_entry(tmp_path):
    entry = push_notification("lock", "dev.env locked", base_dir=tmp_path)
    assert entry["event"] == "lock"
    assert entry["detail"] == "dev.env locked"
    entries = load_notifications(tmp_path)
    assert len(entries) == 1
    assert entries[0] == entry


def test_push_notification_accumulates(tmp_path):
    push_notification("lock", "a", base_dir=tmp_path)
    push_notification("unlock", "b", base_dir=tmp_path)
    entries = list_notifications(tmp_path)
    assert len(entries) == 2
    assert entries[1]["event"] == "unlock"


def test_clear_notifications_returns_count(tmp_path):
    push_notification("lock", "a", base_dir=tmp_path)
    push_notification("lock", "b", base_dir=tmp_path)
    count = clear_notifications(tmp_path)
    assert count == 2
    assert load_notifications(tmp_path) == []


def test_list_notifications_empty(tmp_path):
    assert list_notifications(tmp_path) == []
