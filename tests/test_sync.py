"""Tests for envcrypt.sync."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envcrypt.sync import sync_env_file, list_synced_files, SyncError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RECIPIENTS = {
    "alice": "age1alice000",
    "bob": "age1bob0000",
}


# ---------------------------------------------------------------------------
# sync_env_file
# ---------------------------------------------------------------------------

class TestSyncEnvFile:
    def test_raises_when_env_file_missing(self, tmp_path):
        with pytest.raises(SyncError, match="env file not found"):
            sync_env_file(str(tmp_path / "nonexistent.env"))

    def test_raises_when_recipients_load_fails(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        with patch("envcrypt.sync.load_recipients", side_effect=Exception("bad json")):
            with pytest.raises(SyncError, match="failed to load recipients"):
                sync_env_file(str(env))

    def test_raises_when_no_recipients(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        with patch("envcrypt.sync.load_recipients", return_value={}):
            with pytest.raises(SyncError, match="no recipients"):
                sync_env_file(str(env))

    def test_returns_mapping_on_success(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")

        encrypted_paths = {
            "alice": str(tmp_path / "vault" / "alice.age"),
            "bob": str(tmp_path / "vault" / "bob.age"),
        }

        def fake_get_encrypted_path(name, base=None):
            return Path(encrypted_paths[name])

        with patch("envcrypt.sync.load_recipients", return_value=RECIPIENTS), \
             patch("envcrypt.sync.get_encrypted_path", side_effect=fake_get_encrypted_path), \
             patch("envcrypt.sync.lock") as mock_lock:

            result = sync_env_file(str(env))

        assert result == encrypted_paths
        assert mock_lock.call_count == 2

    def test_lock_called_with_correct_args(self, tmp_path):
        """Verify lock is invoked with the env path, recipient key, and output path."""
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        out = tmp_path / "vault" / "alice.age"

        with patch("envcrypt.sync.load_recipients", return_value={"alice": "age1alice000"}), \
             patch("envcrypt.sync.get_encrypted_path", return_value=out), \
             patch("envcrypt.sync.lock") as mock_lock:

            sync_env_file(str(env))

        mock_lock.assert_called_once_with(str(env), "age1alice000", output=str(out))

    def test_raises_on_lock_failure(self, tmp_path):
        from envcrypt.vault import VaultError
        env = tmp_path / ".env"
        env.write_text("KEY=val")

        with patch("envcrypt.sync.load_recipients", return_value=RECIPIENTS), \
             patch("envcrypt.sync.get_encrypted_path", return_value=tmp_path / "out.age"), \
             patch("envcrypt.sync.lock", side_effect=VaultError("age failed")):

            with pytest.raises(SyncError, match="failed to encrypt for recipient"):
                sync_env_file(str(env))


# ---------------------------------------------------------------------------
# list_synced_files
# ---------------------------------------------------------------------------

class TestListSyncedFiles:
    def test_returns_empty_when_vault_missing(self):
        with patch("envcrypt.sync.get_vault_dir", return_value=Path("/nonexistent/vault")):
            assert list_synced_files() == {}
