"""Tests for envcrypt.env_encrypt_partial."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envcrypt.env_encrypt_partial import (
    PartialEncryptError,
    encrypt_keys,
    list_encrypted_keys,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret\nDEBUG=true\n")
    return p


# ---------------------------------------------------------------------------
# list_encrypted_keys
# ---------------------------------------------------------------------------

def test_list_encrypted_keys_empty_when_none_encrypted(env_file: Path) -> None:
    assert list_encrypted_keys(env_file) == []


def test_list_encrypted_keys_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(PartialEncryptError, match="env file not found"):
        list_encrypted_keys(tmp_path / "missing.env")


def test_list_encrypted_keys_returns_marked_keys(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("DB_PASS=ENC[deadbeef]\nDEBUG=true\n")
    assert list_encrypted_keys(p) == ["DB_PASS"]


# ---------------------------------------------------------------------------
# encrypt_keys – error paths
# ---------------------------------------------------------------------------

def test_raises_when_env_file_missing(tmp_path: Path) -> None:
    with pytest.raises(PartialEncryptError, match="env file not found"):
        encrypt_keys(tmp_path / "missing.env", ["KEY"], ["age1abc"])


def test_raises_when_no_keys_specified(env_file: Path) -> None:
    with pytest.raises(PartialEncryptError, match="no keys specified"):
        encrypt_keys(env_file, [], ["age1abc"])


def test_raises_when_no_recipients(env_file: Path) -> None:
    with pytest.raises(PartialEncryptError, match="no recipients"):
        encrypt_keys(env_file, ["DB_PASS"], [])


def test_raises_when_encryption_fails(env_file: Path) -> None:
    from envcrypt.crypto import AgeEncryptionError

    with patch("envcrypt.env_encrypt_partial.encrypt_file", side_effect=AgeEncryptionError("boom")):
        with pytest.raises(PartialEncryptError, match="encryption failed for key"):
            encrypt_keys(env_file, ["DB_PASS"], ["age1abc"])


# ---------------------------------------------------------------------------
# encrypt_keys – happy path
# ---------------------------------------------------------------------------

def _fake_encrypt(src: Path, dest: Path, recipients: list) -> None:  # noqa: ARG001
    """Stub: write a deterministic fake ciphertext."""
    dest.write_bytes(b"FAKECIPHERTEXT")


def test_encrypts_selected_key(env_file: Path) -> None:
    with patch("envcrypt.env_encrypt_partial.encrypt_file", side_effect=_fake_encrypt):
        mapping = encrypt_keys(env_file, ["DB_PASS"], ["age1abc"], dest=env_file)
    assert "DB_PASS" in mapping
    assert mapping["DB_PASS"].startswith("ENC[")


def test_unselected_keys_unchanged(env_file: Path) -> None:
    dest = env_file.parent / "out.env"
    with patch("envcrypt.env_encrypt_partial.encrypt_file", side_effect=_fake_encrypt):
        encrypt_keys(env_file, ["DB_PASS"], ["age1abc"], dest=dest)
    content = dest.read_text()
    assert "DB_HOST=localhost" in content
    assert "DEBUG=true" in content


def test_already_encrypted_key_skipped(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("DB_PASS=ENC[deadbeef]\n")
    with patch("envcrypt.env_encrypt_partial.encrypt_file", side_effect=_fake_encrypt) as mock_enc:
        mapping = encrypt_keys(p, ["DB_PASS"], ["age1abc"])
    mock_enc.assert_not_called()
    assert mapping["DB_PASS"] == "ENC[deadbeef]"


def test_encrypted_keys_appear_in_list_after_encrypt(env_file: Path) -> None:
    with patch("envcrypt.env_encrypt_partial.encrypt_file", side_effect=_fake_encrypt):
        encrypt_keys(env_file, ["DB_PASS"], ["age1abc"], dest=env_file)
    assert "DB_PASS" in list_encrypted_keys(env_file)
