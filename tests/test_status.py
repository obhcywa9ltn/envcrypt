"""Tests for envcrypt.status."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from envcrypt.status import FileStatus, VaultStatus, _file_status, get_vault_status


# ---------------------------------------------------------------------------
# _file_status
# ---------------------------------------------------------------------------

class TestFileStatus:
    def test_both_missing(self, tmp_path):
        env_p = tmp_path / ".env"
        enc_p = tmp_path / "vault" / ".env.age"
        fs = _file_status("default", env_p, enc_p)
        assert fs.env_exists is False
        assert fs.encrypted_exists is False
        assert fs.in_sync is False

    def test_only_env_exists(self, tmp_path):
        env_p = tmp_path / ".env"
        env_p.write_text("KEY=val")
        enc_p = tmp_path / ".env.age"
        fs = _file_status("default", env_p, enc_p)
        assert fs.env_exists is True
        assert fs.encrypted_exists is False
        assert fs.in_sync is False

    def test_only_encrypted_exists(self, tmp_path):
        env_p = tmp_path / ".env"
        enc_p = tmp_path / ".env.age"
        enc_p.write_bytes(b"age-encrypted")
        fs = _file_status("default", env_p, enc_p)
        assert fs.env_exists is False
        assert fs.encrypted_exists is True
        assert fs.in_sync is False

    def test_in_sync_when_encrypted_newer(self, tmp_path):
        env_p = tmp_path / ".env"
        env_p.write_text("KEY=val")
        time.sleep(0.01)
        enc_p = tmp_path / ".env.age"
        enc_p.write_bytes(b"age-encrypted")
        fs = _file_status("default", env_p, enc_p)
        assert fs.in_sync is True

    def test_not_in_sync_when_env_newer(self, tmp_path):
        enc_p = tmp_path / ".env.age"
        enc_p.write_bytes(b"age-encrypted")
        time.sleep(0.01)
        env_p = tmp_path / ".env"
        env_p.write_text("KEY=val")
        fs = _file_status("default", env_p, enc_p)
        assert fs.in_sync is False


# ---------------------------------------------------------------------------
# VaultStatus
# ---------------------------------------------------------------------------

class TestVaultStatus:
    def test_all_in_sync_true(self):
        fs = FileStatus(
            name="a", env_path=Path("a"), encrypted_path=Path("a.age"),
            env_exists=True, encrypted_exists=True, in_sync=True,
        )
        vs = VaultStatus(tracked=[fs])
        assert vs.all_in_sync is True

    def test_all_in_sync_false(self):
        fs = FileStatus(
            name="a", env_path=Path("a"), encrypted_path=Path("a.age"),
            env_exists=True, encrypted_exists=False, in_sync=False,
        )
        vs = VaultStatus(tracked=[fs])
        assert vs.all_in_sync is False

    def test_empty_tracked_is_in_sync(self):
        vs = VaultStatus()
        assert vs.all_in_sync is True


# ---------------------------------------------------------------------------
# get_vault_status
# ---------------------------------------------------------------------------

class TestGetVaultStatus:
    def test_returns_vault_status_with_entries(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value")
        synced = {"default": str(env_file)}

        with patch("envcrypt.status.list_synced_files", return_value=synced), \
             patch("envcrypt.status.get_vault_dir", return_value=tmp_path):
            vs = get_vault_status(base_dir=tmp_path)

        assert len(vs.tracked) == 1
        assert vs.tracked[0].name == "default"

    def test_returns_empty_when_no_synced_files(self, tmp_path):
        with patch("envcrypt.status.list_synced_files", return_value={}), \
             patch("envcrypt.status.get_vault_dir", return_value=tmp_path):
            vs = get_vault_status(base_dir=tmp_path)

        assert vs.tracked == []
        assert vs.all_in_sync is True
