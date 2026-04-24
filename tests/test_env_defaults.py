"""Tests for envcrypt.env_defaults."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcrypt.env_defaults import (
    DefaultsError,
    apply_defaults,
    get_defaults_path,
    load_defaults,
    remove_default,
    save_defaults,
    set_default,
)


def test_get_defaults_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_defaults_path() == tmp_path / ".envcrypt" / "defaults.json"


def test_get_defaults_path_uses_base_dir(tmp_path):
    assert get_defaults_path(tmp_path) == tmp_path / ".envcrypt" / "defaults.json"


def test_load_defaults_returns_empty_when_missing(tmp_path):
    assert load_defaults(tmp_path) == {}


def test_load_defaults_parses_valid_file(tmp_path):
    path = get_defaults_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"FOO": "bar", "PORT": "8080"}))
    result = load_defaults(tmp_path)
    assert result == {"FOO": "bar", "PORT": "8080"}


def test_load_defaults_raises_on_invalid_json(tmp_path):
    path = get_defaults_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with pytest.raises(DefaultsError, match="Invalid JSON"):
        load_defaults(tmp_path)


def test_load_defaults_raises_when_root_is_not_dict(tmp_path):
    path = get_defaults_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(["a", "b"]))
    with pytest.raises(DefaultsError, match="JSON object"):
        load_defaults(tmp_path)


def test_save_and_load_roundtrip(tmp_path):
    data = {"KEY": "value", "NUM": "42"}
    save_defaults(data, tmp_path)
    assert load_defaults(tmp_path) == data


def test_set_default_adds_new_key(tmp_path):
    result = set_default("MY_KEY", "my_value", tmp_path)
    assert result["MY_KEY"] == "my_value"
    assert load_defaults(tmp_path)["MY_KEY"] == "my_value"


def test_set_default_overwrites_existing(tmp_path):
    set_default("KEY", "old", tmp_path)
    set_default("KEY", "new", tmp_path)
    assert load_defaults(tmp_path)["KEY"] == "new"


def test_remove_default_deletes_key(tmp_path):
    set_default("KEY", "val", tmp_path)
    remove_default("KEY", tmp_path)
    assert "KEY" not in load_defaults(tmp_path)


def test_remove_default_raises_when_key_missing(tmp_path):
    with pytest.raises(DefaultsError, match="not found"):
        remove_default("NONEXISTENT", tmp_path)


def test_apply_defaults_raises_when_env_missing(tmp_path):
    set_default("FOO", "bar", tmp_path)
    with pytest.raises(DefaultsError, match="Env file not found"):
        apply_defaults(tmp_path / ".env", tmp_path)


def test_apply_defaults_fills_missing_keys(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING=yes\n")
    set_default("EXISTING", "no", tmp_path)
    set_default("NEW_KEY", "default_val", tmp_path)
    applied = apply_defaults(env_file, tmp_path)
    assert "NEW_KEY" in applied
    assert "EXISTING" not in applied
    content = env_file.read_text()
    assert "NEW_KEY=default_val" in content
    assert content.count("EXISTING") == 1


def test_apply_defaults_returns_empty_when_no_defaults(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    applied = apply_defaults(env_file, tmp_path)
    assert applied == {}


def test_apply_defaults_returns_empty_when_all_present(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    set_default("FOO", "baz", tmp_path)
    applied = apply_defaults(env_file, tmp_path)
    assert applied == {}
    assert "FOO=bar" in env_file.read_text()
