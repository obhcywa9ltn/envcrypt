"""Tests for envcrypt.tag."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcrypt.tag import (
    TagError,
    add_tag,
    get_tags_path,
    list_tags,
    load_tags,
    remove_tag,
    save_tags,
)


class TestGetTagsPath:
    def test_defaults_to_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert get_tags_path() == tmp_path / ".envcrypt_tags.json"

    def test_uses_provided_base_dir(self, tmp_path):
        assert get_tags_path(tmp_path) == tmp_path / ".envcrypt_tags.json"


class TestLoadTags:
    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        assert load_tags(tmp_path) == {}

    def test_loads_valid_file(self, tmp_path):
        data = {"prod": ["stable", "reviewed"]}
        (tmp_path / ".envcrypt_tags.json").write_text(json.dumps(data))
        assert load_tags(tmp_path) == data

    def test_raises_on_invalid_json(self, tmp_path):
        (tmp_path / ".envcrypt_tags.json").write_text("not json")
        with pytest.raises(TagError, match="Invalid JSON"):
            load_tags(tmp_path)

    def test_raises_when_root_is_not_dict(self, tmp_path):
        (tmp_path / ".envcrypt_tags.json").write_text(json.dumps(["a", "b"]))
        with pytest.raises(TagError, match="root must be a JSON object"):
            load_tags(tmp_path)

    def test_raises_when_value_is_not_list(self, tmp_path):
        (tmp_path / ".envcrypt_tags.json").write_text(json.dumps({"prod": "stable"}))
        with pytest.raises(TagError, match="must be a list"):
            load_tags(tmp_path)


class TestAddTag:
    def test_adds_new_tag(self, tmp_path):
        result = add_tag("prod", "stable", base_dir=tmp_path)
        assert "stable" in result["prod"]

    def test_idempotent_when_tag_already_present(self, tmp_path):
        add_tag("prod", "stable", base_dir=tmp_path)
        result = add_tag("prod", "stable", base_dir=tmp_path)
        assert result["prod"].count("stable") == 1

    def test_persists_to_disk(self, tmp_path):
        add_tag("dev", "wip", base_dir=tmp_path)
        on_disk = json.loads((tmp_path / ".envcrypt_tags.json").read_text())
        assert "wip" in on_disk["dev"]


class TestRemoveTag:
    def test_removes_existing_tag(self, tmp_path):
        add_tag("prod", "stable", base_dir=tmp_path)
        result = remove_tag("prod", "stable", base_dir=tmp_path)
        assert "prod" not in result

    def test_raises_when_tag_not_present(self, tmp_path):
        with pytest.raises(TagError, match="not found"):
            remove_tag("prod", "nonexistent", base_dir=tmp_path)

    def test_removes_only_specified_tag(self, tmp_path):
        add_tag("prod", "stable", base_dir=tmp_path)
        add_tag("prod", "reviewed", base_dir=tmp_path)
        result = remove_tag("prod", "stable", base_dir=tmp_path)
        assert "reviewed" in result["prod"]


class TestListTags:
    def test_returns_empty_list_when_no_tags(self, tmp_path):
        assert list_tags("prod", base_dir=tmp_path) == []

    def test_returns_tags_for_key(self, tmp_path):
        add_tag("prod", "stable", base_dir=tmp_path)
        assert list_tags("prod", base_dir=tmp_path) == ["stable"]
