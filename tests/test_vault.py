"""Tests for envcrypt.vault."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envcrypt.crypto import AgeEncryptionError
from envcrypt.recipients import RecipientsError
from envcrypt.vault import (
    VaultError,
    get_encrypted_path,
    get_vault_dir,
    lock,
    unlock,
)


# ---------------------------------------------------------------------------
# get_vault_dir
# ---------------------------------------------------------------------------

class TestGetVaultDir:
    def test_returns_default_relative_to_cwd(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ENVCRYPT_VAULT_DIR", raising=False)
        monkeypatch.chdir(tmp_path)
        assert get_vault_dir() == tmp_path / ".envcrypt"

    def test_returns_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ENVCRYPT_VAULT_DIR", str(tmp_path / "custom"))
        assert get_vault_dir() == tmp_path / "custom"

    def test_returns_base_subdir_when_provided(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ENVCRYPT_VAULT_DIR", raising=False)
        assert get_vault_dir(base=tmp_path) == tmp_path / ".envcrypt"


# ---------------------------------------------------------------------------
# get_encrypted_path
# ---------------------------------------------------------------------------

class TestGetEncryptedPath:
    def test_appends_age_extension(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ENVCRYPT_VAULT_DIR", raising=False)
        monkeypatch.chdir(tmp_path)
        result = get_encrypted_path(".env", vault_dir=tmp_path)
        assert result == tmp_path / ".env.age"

    def test_uses_only_filename(self, tmp_path):
        result = get_encrypted_path("/some/deep/path/.env", vault_dir=tmp_path)
        assert result == tmp_path / ".env.age"


# ---------------------------------------------------------------------------
# lock
# ---------------------------------------------------------------------------

class TestLock:
    def test_raises_when_env_file_missing(self, tmp_path):
        with pytest.raises(VaultError, match="env file not found"):
            lock(tmp_path / "missing.env", tmp_path / "recipients.json")

    def test_raises_when_recipients_load_fails(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        with patch("envcrypt.vault.load_recipients", side_effect=RecipientsError("bad")):
            with pytest.raises(VaultError, match="failed to load recipients"):
                lock(env, tmp_path / "recipients.json")

    def test_raises_when_no_recipients(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        with patch("envcrypt.vault.load_recipients", return_value={}):
            with pytest.raises(VaultError, match="no recipients"):
                lock(env, tmp_path / "recipients.json")

    def test_raises_when_encryption_fails(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        with patch("envcrypt.vault.load_recipients", return_value={"alice": "age1abc"}), \
             patch("envcrypt.vault.encrypt_file", side_effect=AgeEncryptionError("oops")):
            with pytest.raises(VaultError, match="encryption failed"):
                lock(env, tmp_path / "recipients.json", vault_dir=tmp_path)

    def test_returns_output_path_on_success(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val")
        with patch("envcrypt.vault.load_recipients", return_value={"alice": "age1abc"}), \
             patch("envcrypt.vault.encrypt_file") as mock_enc:
            result = lock(env, tmp_path / "recipients.json", vault_dir=tmp_path)
        assert result == tmp_path / ".env.age"
        mock_enc.assert_called_once()


# ---------------------------------------------------------------------------
# unlock
# ---------------------------------------------------------------------------

class TestUnlock:
    def test_raises_when_encrypted_file_missing(self, tmp_path):
        with pytest.raises(VaultError, match="encrypted file not found"):
            unlock(tmp_path / "missing.env.age", tmp_path / "key.txt")

    def test_raises_when_decryption_fails(self, tmp_path):
        enc = tmp_path / ".env.age"
        enc.write_bytes(b"fake")
        with patch("envcrypt.vault.decrypt_file", side_effect=AgeEncryptionError("bad key")):
            with pytest.raises(VaultError, match="decryption failed"):
                unlock(enc, tmp_path / "key.txt", output=tmp_path / ".env")

    def test_returns_output_path_on_success(self, tmp_path):
        enc = tmp_path / ".env.age"
        enc.write_bytes(b"fake")
        out = tmp_path / ".env"
        with patch("envcrypt.vault.decrypt_file") as mock_dec:
            result = unlock(enc, tmp_path / "key.txt", output=out)
        assert result == out
        mock_dec.assert_called_once()

    def test_derives_output_name_from_encrypted_stem(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        enc = tmp_path / ".env.age"
        enc.write_bytes(b"fake")
        with patch("envcrypt.vault.decrypt_file"):
            result = unlock(enc, tmp_path / "key.txt")
        assert result == tmp_path / ".env"
