"""Tests for envcrypt.env_required."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envcrypt.env_required import (
    RequiredError,
    add_required_key,
    check_required,
    get_required_path,
    load_required,
    remove_required_key,
    save_required,
)


# ---------------------------------------------------------------------------
# get_required_path
# ---------------------------------------------------------------------------

def test_get_required_path_defaults_to_cwd():
    path = get_required_path()
    assert path == Path.cwd() / ".envcrypt" / "required.json"


def test_get_required_path_uses_base_dir(tmp_path):
    path = get_required_path(str(tmp_path))
    assert path == tmp_path / ".envcrypt" / "required.json"


# ---------------------------------------------------------------------------
# load_required
# ---------------------------------------------------------------------------

def test_load_required_returns_empty_when_missing(tmp_path):
    assert load_required(str(tmp_path)) == []


def test_load_required_parses_valid_file(tmp_path):
    p = tmp_path / ".envcrypt" / "required.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(["DB_URL", "SECRET_KEY"]))
    assert load_required(str(tmp_path)) == ["DB_URL", "SECRET_KEY"]


def test_load_required_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "required.json"
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(RequiredError, match="Invalid JSON"):
        load_required(str(tmp_path))


def test_load_required_raises_when_root_is_not_list(tmp_path):
    p = tmp_path / ".envcrypt" / "required.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"key": "value"}))
    with pytest.raises(RequiredError, match="JSON array"):
        load_required(str(tmp_path))


# ---------------------------------------------------------------------------
# add_required_key / remove_required_key
# ---------------------------------------------------------------------------

def test_add_required_key_persists(tmp_path):
    keys = add_required_key("API_KEY", str(tmp_path))
    assert "API_KEY" in keys
    assert "API_KEY" in load_required(str(tmp_path))


def test_add_required_key_is_idempotent(tmp_path):
    add_required_key("API_KEY", str(tmp_path))
    keys = add_required_key("API_KEY", str(tmp_path))
    assert keys.count("API_KEY") == 1


def test_remove_required_key_removes_entry(tmp_path):
    save_required(["DB_URL", "SECRET_KEY"], str(tmp_path))
    keys = remove_required_key("DB_URL", str(tmp_path))
    assert "DB_URL" not in keys
    assert "SECRET_KEY" in keys


def test_remove_required_key_raises_when_not_present(tmp_path):
    with pytest.raises(RequiredError, match="not in the required list"):
        remove_required_key("MISSING", str(tmp_path))


# ---------------------------------------------------------------------------
# check_required
# ---------------------------------------------------------------------------

def _write_env(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_check_required_raises_when_env_missing(tmp_path):
    with pytest.raises(RequiredError, match="not found"):
        check_required(str(tmp_path / ".env"), str(tmp_path))


def test_check_required_ok_when_all_present(tmp_path):
    env = tmp_path / ".env"
    _write_env(env, "DB_URL=postgres://localhost\nSECRET_KEY=abc\n")
    save_required(["DB_URL", "SECRET_KEY"], str(tmp_path))
    result = check_required(str(env), str(tmp_path))
    assert result.ok
    assert set(result.present) == {"DB_URL", "SECRET_KEY"}
    assert result.missing == []


def test_check_required_reports_missing(tmp_path):
    env = tmp_path / ".env"
    _write_env(env, "DB_URL=postgres://localhost\n")
    save_required(["DB_URL", "SECRET_KEY"], str(tmp_path))
    result = check_required(str(env), str(tmp_path))
    assert not result.ok
    assert "SECRET_KEY" in result.missing
    assert "DB_URL" in result.present


def test_check_required_ok_when_no_required_keys(tmp_path):
    env = tmp_path / ".env"
    _write_env(env, "FOO=bar\n")
    result = check_required(str(env), str(tmp_path))
    assert result.ok
