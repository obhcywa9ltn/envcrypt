"""Tests for envcrypt/profile.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcrypt.profile import (
    ProfileError,
    add_profile,
    get_profiles_path,
    list_profiles,
    load_profiles,
    remove_profile,
    save_profiles,
    update_profile,
)


# ---------------------------------------------------------------------------
# get_profiles_path
# ---------------------------------------------------------------------------

class TestGetProfilesPath:
    def test_defaults_to_cwd(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        assert get_profiles_path() == tmp_path / ".envcrypt_profiles.json"

    def test_uses_provided_base_dir(self, tmp_path):
        assert get_profiles_path(tmp_path) == tmp_path / ".envcrypt_profiles.json"


# ---------------------------------------------------------------------------
# load_profiles
# ---------------------------------------------------------------------------

class TestLoadProfiles:
    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        assert load_profiles(tmp_path) == {}

    def test_loads_valid_file(self, tmp_path):
        data = {"dev": ".env.dev", "prod": ".env.prod"}
        (tmp_path / ".envcrypt_profiles.json").write_text(json.dumps(data))
        assert load_profiles(tmp_path) == data

    def test_raises_on_invalid_json(self, tmp_path):
        (tmp_path / ".envcrypt_profiles.json").write_text("not json")
        with pytest.raises(ProfileError, match="not valid JSON"):
            load_profiles(tmp_path)

    def test_raises_when_root_is_not_dict(self, tmp_path):
        (tmp_path / ".envcrypt_profiles.json").write_text(json.dumps(["dev"]))
        with pytest.raises(ProfileError, match="root must be a JSON object"):
            load_profiles(tmp_path)

    def test_raises_when_entry_value_not_string(self, tmp_path):
        (tmp_path / ".envcrypt_profiles.json").write_text(json.dumps({"dev": 123}))
        with pytest.raises(ProfileError, match="string name to a string path"):
            load_profiles(tmp_path)


# ---------------------------------------------------------------------------
# add_profile / update_profile / remove_profile
# ---------------------------------------------------------------------------

class TestAddProfile:
    def test_adds_new_profile(self, tmp_path):
        result = add_profile("dev", ".env.dev", tmp_path)
        assert result == {"dev": ".env.dev"}

    def test_persists_to_disk(self, tmp_path):
        add_profile("dev", ".env.dev", tmp_path)
        on_disk = json.loads((tmp_path / ".envcrypt_profiles.json").read_text())
        assert on_disk == {"dev": ".env.dev"}

    def test_raises_when_profile_already_exists(self, tmp_path):
        add_profile("dev", ".env.dev", tmp_path)
        with pytest.raises(ProfileError, match="already exists"):
            add_profile("dev", ".env.dev2", tmp_path)


class TestUpdateProfile:
    def test_updates_existing_profile(self, tmp_path):
        add_profile("dev", ".env.dev", tmp_path)
        result = update_profile("dev", ".env.dev.new", tmp_path)
        assert result["dev"] == ".env.dev.new"

    def test_raises_when_profile_missing(self, tmp_path):
        with pytest.raises(ProfileError, match="does not exist"):
            update_profile("ghost", ".env.ghost", tmp_path)


class TestRemoveProfile:
    def test_removes_existing_profile(self, tmp_path):
        add_profile("dev", ".env.dev", tmp_path)
        result = remove_profile("dev", tmp_path)
        assert "dev" not in result

    def test_raises_when_profile_missing(self, tmp_path):
        with pytest.raises(ProfileError, match="does not exist"):
            remove_profile("ghost", tmp_path)


# ---------------------------------------------------------------------------
# list_profiles
# ---------------------------------------------------------------------------

def test_list_profiles_returns_sorted_names(tmp_path):
    save_profiles({"prod": ".env.prod", "dev": ".env.dev", "staging": ".env.staging"}, tmp_path)
    assert list_profiles(tmp_path) == ["dev", "prod", "staging"]


def test_list_profiles_empty_when_no_file(tmp_path):
    assert list_profiles(tmp_path) == []
