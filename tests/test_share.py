"""Tests for envcrypt.share."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envcrypt.share import ShareError, share_with, receive_share, list_shares
from envcrypt.crypto import AgeEncryptionError
from envcrypt.recipients import RecipientsError


# ---------------------------------------------------------------------------
# share_with
# ---------------------------------------------------------------------------

class TestShareWith:
    def test_raises_when_env_file_missing(self, tmp_path):
        with pytest.raises(ShareError, match="env file not found"):
            share_with(tmp_path / "missing.env", ["alice"], tmp_path / "out")

    def test_raises_when_recipients_load_fails(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val")
        with patch("envcrypt.share.load_recipients", side_effect=RecipientsError("bad")):
            with pytest.raises(ShareError, match="bad"):
                share_with(env_file, ["alice"], tmp_path / "out")

    def test_raises_for_unknown_recipient(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val")
        with patch("envcrypt.share.load_recipients", return_value={"bob": "age1bob"}):
            with pytest.raises(ShareError, match="unknown recipients"):
                share_with(env_file, ["alice"], tmp_path / "out")

    def test_raises_when_encryption_fails(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val")
        with patch("envcrypt.share.load_recipients", return_value={"alice": "age1alice"}), \
             patch("envcrypt.share.encrypt_file", side_effect=AgeEncryptionError("oops")):
            with pytest.raises(ShareError, match="encryption failed for alice"):
                share_with(env_file, ["alice"], tmp_path / "out")

    def test_returns_mapping_on_success(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val")
        out_dir = tmp_path / "shares"
        with patch("envcrypt.share.load_recipients", return_value={"alice": "age1alice", "bob": "age1bob"}), \
             patch("envcrypt.share.encrypt_file") as mock_enc:
            result = share_with(env_file, ["alice", "bob"], out_dir)
        assert "alice" in result
        assert "bob" in result
        assert result["alice"] == out_dir / ".env.alice.age"
        assert mock_enc.call_count == 2


# ---------------------------------------------------------------------------
# receive_share
# ---------------------------------------------------------------------------

class TestReceiveShare:
    def test_raises_when_shared_file_missing(self, tmp_path):
        with pytest.raises(ShareError, match="shared file not found"):
            receive_share(tmp_path / "missing.age", tmp_path / "key.txt", tmp_path / ".env")

    def test_raises_when_key_missing(self, tmp_path):
        shared = tmp_path / "file.age"
        shared.write_bytes(b"data")
        with pytest.raises(ShareError, match="private key not found"):
            receive_share(shared, tmp_path / "missing_key.txt", tmp_path / ".env")

    def test_raises_when_decryption_fails(self, tmp_path):
        shared = tmp_path / "file.age"
        shared.write_bytes(b"data")
        key = tmp_path / "key.txt"
        key.write_text("AGE-SECRET-KEY-1")
        with patch("envcrypt.share.decrypt_file", side_effect=AgeEncryptionError("bad key")):
            with pytest.raises(ShareError, match="decryption failed"):
                receive_share(shared, key, tmp_path / ".env")

    def test_returns_dest_on_success(self, tmp_path):
        shared = tmp_path / "file.age"
        shared.write_bytes(b"data")
        key = tmp_path / "key.txt"
        key.write_text("AGE-SECRET-KEY-1")
        dest = tmp_path / "out" / ".env"
        with patch("envcrypt.share.decrypt_file") as mock_dec:
            result = receive_share(shared, key, dest)
        assert result == dest
        mock_dec.assert_called_once()


# ---------------------------------------------------------------------------
# list_shares
# ---------------------------------------------------------------------------

def test_list_shares_returns_empty_when_dir_missing(tmp_path):
    assert list_shares(tmp_path / "nonexistent") == []


def test_list_shares_returns_age_files(tmp_path):
    share_dir = tmp_path / "shares"
    share_dir.mkdir()
    (share_dir / "a.age").write_bytes(b"")
    (share_dir / "b.age").write_bytes(b"")
    (share_dir / "notes.txt").write_text("ignored")
    result = list_shares(share_dir)
    assert len(result) == 2
    assert all(p.suffix == ".age" for p in result)
