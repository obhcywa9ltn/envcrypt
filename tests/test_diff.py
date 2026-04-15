"""Tests for envcrypt.diff."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envcrypt.diff import DiffError, _parse_env_file, diff_env


# ---------------------------------------------------------------------------
# _parse_env_file
# ---------------------------------------------------------------------------


def test_parse_env_ignores_comments_and_blanks(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("# comment\n\nFOO=bar\nBAZ=qux\n")
    result = _parse_env_file(env)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_handles_equals_in_value(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("KEY=val=ue\n")
    result = _parse_env_file(env)
    assert result == {"KEY": "val=ue"}


def test_parse_env_skips_lines_without_equals(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("NOEQUALS\nFOO=bar\n")
    result = _parse_env_file(env)
    assert result == {"FOO": "bar"}


# ---------------------------------------------------------------------------
# diff_env – error paths
# ---------------------------------------------------------------------------


def test_raises_when_env_file_missing(tmp_path: Path):
    with pytest.raises(DiffError, match="Local env file not found"):
        diff_env(tmp_path / "missing.env", tmp_path / "key.txt")


def test_raises_when_encrypted_file_missing(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")

    with patch("envcrypt.diff.get_encrypted_path", return_value=str(tmp_path / "vault" / "missing.age")):
        with pytest.raises(DiffError, match="No encrypted counterpart found"):
            diff_env(env, tmp_path / "key.txt")


def test_raises_when_unlock_fails(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    encrypted = tmp_path / "vault.age"
    encrypted.write_text("fake")

    from envcrypt.vault import VaultError

    with patch("envcrypt.diff.get_encrypted_path", return_value=str(encrypted)):
        with patch("envcrypt.diff.unlock", side_effect=VaultError("bad key")):
            with pytest.raises(DiffError, match="Failed to decrypt vault file"):
                diff_env(env, tmp_path / "key.txt")


# ---------------------------------------------------------------------------
# diff_env – success paths
# ---------------------------------------------------------------------------


def _make_diff_env(tmp_path: Path, local_content: str, vault_content: str):
    """Helper: patch get_encrypted_path + unlock to return vault_content."""
    env = tmp_path / ".env"
    env.write_text(local_content)
    encrypted = tmp_path / "vault.age"
    encrypted.write_text("fake-encrypted")

    def fake_unlock(enc_path, out_path, key_path):
        Path(out_path).write_text(vault_content)

    with patch("envcrypt.diff.get_encrypted_path", return_value=str(encrypted)):
        with patch("envcrypt.diff.unlock", side_effect=fake_unlock):
            return diff_env(env, tmp_path / "key.txt")


def test_detects_added_keys(tmp_path: Path):
    added, removed, changed = _make_diff_env(tmp_path, "FOO=1\nNEW=2\n", "FOO=1\n")
    assert "NEW" in added
    assert not removed
    assert not changed


def test_detects_removed_keys(tmp_path: Path):
    added, removed, changed = _make_diff_env(tmp_path, "FOO=1\n", "FOO=1\nOLD=9\n")
    assert "OLD" in removed
    assert not added
    assert not changed


def test_detects_changed_values(tmp_path: Path):
    added, removed, changed = _make_diff_env(tmp_path, "FOO=new\n", "FOO=old\n")
    assert "FOO" in changed
    assert changed["FOO"] == ("new", "old")


def test_no_diff_when_identical(tmp_path: Path):
    added, removed, changed = _make_diff_env(tmp_path, "FOO=bar\n", "FOO=bar\n")
    assert not added
    assert not removed
    assert not changed
