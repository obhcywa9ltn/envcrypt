"""Tests for envcrypt.config."""

import json
import pytest
from pathlib import Path

from envcrypt.config import (
    ConfigError,
    get_config_path,
    load_config,
    save_config,
    set_config_value,
    get_config_value,
    CONFIG_FILENAME,
)


class TestGetConfigPath:
    def test_defaults_to_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = get_config_path()
        assert result == tmp_path / CONFIG_FILENAME

    def test_uses_provided_base_dir(self, tmp_path):
        result = get_config_path(tmp_path)
        assert result == tmp_path / CONFIG_FILENAME


class TestLoadConfig:
    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        result = load_config(tmp_path)
        assert result == {}

    def test_loads_valid_config(self, tmp_path):
        data = {"vault_dir": ".envcrypt", "version": 1}
        (tmp_path / CONFIG_FILENAME).write_text(json.dumps(data))
        result = load_config(tmp_path)
        assert result == data

    def test_raises_on_invalid_json(self, tmp_path):
        (tmp_path / CONFIG_FILENAME).write_text("not json{{")
        with pytest.raises(ConfigError, match="Invalid JSON"):
            load_config(tmp_path)

    def test_raises_when_root_is_not_dict(self, tmp_path):
        (tmp_path / CONFIG_FILENAME).write_text(json.dumps([1, 2, 3]))
        with pytest.raises(ConfigError, match="root must be a JSON object"):
            load_config(tmp_path)


class TestSaveConfig:
    def test_writes_json_file(self, tmp_path):
        config = {"key": "value"}
        path = save_config(config, tmp_path)
        assert path == tmp_path / CONFIG_FILENAME
        stored = json.loads(path.read_text())
        assert stored == config

    def test_returns_path(self, tmp_path):
        result = save_config({}, tmp_path)
        assert isinstance(result, Path)

    def test_raises_on_write_error(self, tmp_path):
        # Make the config path a directory so writing fails
        bad_path = tmp_path / CONFIG_FILENAME
        bad_path.mkdir()
        with pytest.raises(ConfigError, match="Could not write config file"):
            save_config({"a": 1}, tmp_path)


class TestSetAndGetConfigValue:
    def test_set_creates_key(self, tmp_path):
        set_config_value("vault_dir", ".envcrypt", tmp_path)
        stored = json.loads((tmp_path / CONFIG_FILENAME).read_text())
        assert stored["vault_dir"] == ".envcrypt"

    def test_get_returns_stored_value(self, tmp_path):
        set_config_value("version", 2, tmp_path)
        result = get_config_value("version", base_dir=tmp_path)
        assert result == 2

    def test_get_returns_default_when_missing(self, tmp_path):
        result = get_config_value("nonexistent", defaultfallback", base_dir=tmp_path)
        assert result == "fallback"

    def test_set_overwrites_existing_key(self, tmp_path):
        set_config_value(", 1, tmp_path)
        set_config_value("version", 99, tmp_path)
        assert get_config_value("version", base_dir=tmp_path) == 99

    def test_set_preserv tmp_path):
        set_config_value("a", 1, tmp_path)
        set_config_value("b", 2, tmp_path)
        assert get_config_value("a", base_dir=tmp_path) == 1
        assert get_config_value("b", base_dir=tmp_path) == 2
