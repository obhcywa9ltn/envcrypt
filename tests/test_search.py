"""Tests for envcrypt.search."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envcrypt.search import SearchError, SearchMatch, SearchResult, search_vault


AGE_FILES = ["production.age", "staging.age"]

PRODUCTION_PLAIN = "DB_HOST=prod.db\nDB_PASS=secret\nAPI_KEY=abc123\n"
STAGING_PLAIN = "DB_HOST=staging.db\nDEBUG=true\n"


def _make_path(name: str, tmp_path: Path) -> Path:
    p = tmp_path / name
    p.touch()
    return p


@pytest.fixture()
def vault_setup(tmp_path):
    vault = tmp_path / ".envcrypt"
    vault.mkdir()
    (vault / "production.age").touch()
    (vault / "staging.age").touch()
    return tmp_path, vault


def _unlock_side_effect(env_name, base_dir, key_file):
    if env_name == "production":
        return PRODUCTION_PLAIN
    if env_name == "staging":
        return STAGING_PLAIN
    raise RuntimeError("unknown")


def test_raises_when_vault_missing(tmp_path):
    with pytest.raises(SearchError, match="Vault directory not found"):
        search_vault("DB", base_dir=tmp_path, key_file=Path("key.txt"))


def test_raises_on_invalid_pattern(vault_setup):
    base_dir, _ = vault_setup
    with pytest.raises(SearchError, match="Invalid pattern"):
        search_vault("[invalid", base_dir=base_dir, key_file=Path("k"))


def test_returns_matches_for_key_pattern(vault_setup):
    base_dir, _ = vault_setup
    with patch("envcrypt.search.unlock", side_effect=_unlock_side_effect):
        result = search_vault("DB_", base_dir=base_dir, key_file=Path("k"))
    assert result.found
    keys = {m.key for m in result.matches}
    assert "DB_HOST" in keys
    assert "DB_PASS" in keys


def test_skips_unreadable_files(vault_setup):
    base_dir, _ = vault_setup

    def bad_unlock(env_name, base_dir, key_file):
        raise RuntimeError("decrypt failed")

    with patch("envcrypt.search.unlock", side_effect=bad_unlock):
        result = search_vault("DB", base_dir=base_dir, key_file=Path("k"))
    assert not result.found


def test_search_values_flag(vault_setup):
    base_dir, _ = vault_setup
    with patch("envcrypt.search.unlock", side_effect=_unlock_side_effect):
        result = search_vault("secret", base_dir=base_dir, key_file=Path("k"), search_values=True)
    assert result.found
    assert any(m.value == "secret" for m in result.matches)


def test_case_insensitive_match(vault_setup):
    base_dir, _ = vault_setup
    with patch("envcrypt.search.unlock", side_effect=_unlock_side_effect):
        result = search_vault("api_key", base_dir=base_dir, key_file=Path("k"))
    assert result.found
    assert result.matches[0].key == "API_KEY"


def test_no_match_returns_empty(vault_setup):
    base_dir, _ = vault_setup
    with patch("envcrypt.search.unlock", side_effect=_unlock_side_effect):
        result = search_vault("NONEXISTENT", base_dir=base_dir, key_file=Path("k"))
    assert not result.found
    assert result.matches == []
