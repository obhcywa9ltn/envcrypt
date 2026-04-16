"""Tests for envcrypt.history."""
import json
import time
from pathlib import Path

import pytest

from envcrypt.history import (
    HistoryError,
    clear_history,
    get_history_path,
    load_history,
    record_event,
    save_history,
)


def test_get_history_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_history_path() == tmp_path / ".envcrypt" / "history.json"


def test_get_history_path_uses_base_dir(tmp_path):
    assert get_history_path(tmp_path) == tmp_path / ".envcrypt" / "history.json"


def test_load_history_returns_empty_when_missing(tmp_path):
    assert load_history(tmp_path) == []


def test_load_history_parses_valid_file(tmp_path):
    p = tmp_path / ".envcrypt" / "history.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps([{"action": "lock", "env_file": ".env"}]))
    result = load_history(tmp_path)
    assert result[0]["action"] == "lock"


def test_load_history_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "history.json"
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(HistoryError, match="Invalid history file"):
        load_history(tmp_path)


def test_load_history_raises_when_root_not_list(tmp_path):
    p = tmp_path / ".envcrypt" / "history.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"bad": True}))
    with pytest.raises(HistoryError, match="must be a list"):
        load_history(tmp_path)


def test_save_history_creates_parents(tmp_path):
    entries = [{"action": "unlock"}]
    save_history(entries, tmp_path)
    assert (tmp_path / ".envcrypt" / "history.json").exists()


def test_record_event_appends_entry(tmp_path):
    before = time.time()
    entry = record_event("lock", ".env", actor="alice", base_dir=tmp_path)
    after = time.time()
    assert entry["action"] == "lock"
    assert entry["env_file"] == ".env"
    assert entry["actor"] == "alice"
    assert before <= entry["timestamp"] <= after
    assert len(load_history(tmp_path)) == 1


def test_record_event_accumulates_entries(tmp_path):
    record_event("lock", ".env", base_dir=tmp_path)
    record_event("unlock", ".env", base_dir=tmp_path)
    assert len(load_history(tmp_path)) == 2


def test_clear_history_empties_log(tmp_path):
    record_event("lock", ".env", base_dir=tmp_path)
    clear_history(tmp_path)
    assert load_history(tmp_path) == []
