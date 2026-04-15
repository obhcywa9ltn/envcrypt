"""Tests for envcrypt.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcrypt.audit import (
    AuditError,
    append_audit_entry,
    clear_audit_log,
    get_audit_path,
    load_audit_log,
)


class TestGetAuditPath:
    def test_defaults_to_cwd(self, tmp_path: Path) -> None:
        path = get_audit_path(str(tmp_path))
        assert path == tmp_path / ".envcrypt_audit.json"

    def test_uses_provided_base_dir(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        path = get_audit_path(str(sub))
        assert path.parent == sub


class TestLoadAuditLog:
    def test_returns_empty_list_when_file_missing(self, tmp_path: Path) -> None:
        result = load_audit_log(str(tmp_path))
        assert result == []

    def test_loads_valid_log(self, tmp_path: Path) -> None:
        entries = [{"timestamp": "2024-01-01T00:00:00+00:00", "action": "lock", "details": {}}]
        (tmp_path / ".envcrypt_audit.json").write_text(json.dumps(entries))
        result = load_audit_log(str(tmp_path))
        assert result == entries

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / ".envcrypt_audit.json").write_text("not json")
        with pytest.raises(AuditError, match="not valid JSON"):
            load_audit_log(str(tmp_path))

    def test_raises_when_root_is_not_list(self, tmp_path: Path) -> None:
        (tmp_path / ".envcrypt_audit.json").write_text(json.dumps({"bad": True}))
        with pytest.raises(AuditError, match="root must be a JSON array"):
            load_audit_log(str(tmp_path))


class TestAppendAuditEntry:
    def test_creates_entry_with_required_fields(self, tmp_path: Path) -> None:
        entry = append_audit_entry("lock", {"file": ".env"}, base_dir=str(tmp_path))
        assert entry["action"] == "lock"
        assert entry["details"] == {"file": ".env"}
        assert "timestamp" in entry

    def test_persists_entry_to_disk(self, tmp_path: Path) -> None:
        append_audit_entry("unlock", base_dir=str(tmp_path))
        log = load_audit_log(str(tmp_path))
        assert len(log) == 1
        assert log[0]["action"] == "unlock"

    def test_accumulates_multiple_entries(self, tmp_path: Path) -> None:
        append_audit_entry("lock", base_dir=str(tmp_path))
        append_audit_entry("unlock", base_dir=str(tmp_path))
        log = load_audit_log(str(tmp_path))
        assert len(log) == 2

    def test_details_defaults_to_empty_dict(self, tmp_path: Path) -> None:
        entry = append_audit_entry("add", base_dir=str(tmp_path))
        assert entry["details"] == {}


class TestClearAuditLog:
    def test_resets_log_to_empty_list(self, tmp_path: Path) -> None:
        append_audit_entry("lock", base_dir=str(tmp_path))
        clear_audit_log(str(tmp_path))
        log = load_audit_log(str(tmp_path))
        assert log == []

    def test_creates_file_if_missing(self, tmp_path: Path) -> None:
        clear_audit_log(str(tmp_path))
        path = tmp_path / ".envcrypt_audit.json"
        assert path.exists()
        assert json.loads(path.read_text()) == []
