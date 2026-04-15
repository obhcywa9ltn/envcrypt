"""Tests for envcrypt.keys module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from envcrypt.keys import (
    KeyError,
    extract_public_key,
    generate_keypair,
    get_key_dir,
    get_key_file,
    key_exists,
)

AGE_KEY_CONTENT = (
    "# created: 2024-01-01T00:00:00Z\n"
    "# public key: age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq\n"
    "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
)
PUBLIC_KEY = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"


def make_completed_process(returncode=0, stdout="", stderr=""):
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestGetKeyDir:
    def test_returns_default_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("ENVCRYPT_KEY_DIR", raising=False)
        key_dir = get_key_dir()
        assert key_dir == Path.home() / ".config" / "envcrypt"

    def test_returns_env_value_when_set(self, monkeypatch):
        monkeypatch.setenv("ENVCRYPT_KEY_DIR", "/tmp/envcrypt")
        assert get_key_dir() == Path("/tmp/envcrypt")


class TestGetKeyFile:
    def test_returns_default_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("ENVCRYPT_KEY_FILE", raising=False)
        monkeypatch.delenv("ENVCRYPT_KEY_DIR", raising=False)
        assert get_key_file() == Path.home() / ".config" / "envcrypt" / "key.txt"

    def test_returns_env_value_when_set(self, monkeypatch):
        monkeypatch.setenv("ENVCRYPT_KEY_FILE", "/tmp/mykey.txt")
        assert get_key_file() == Path("/tmp/mykey.txt")


class TestKeyExists:
    def test_returns_true_when_file_exists(self, tmp_path):
        key_file = tmp_path / "key.txt"
        key_file.write_text(AGE_KEY_CONTENT)
        assert key_exists(key_file) is True

    def test_returns_false_when_file_missing(self, tmp_path):
        assert key_exists(tmp_path / "missing.txt") is False


class TestExtractPublicKey:
    def test_extracts_public_key(self, tmp_path):
        key_file = tmp_path / "key.txt"
        key_file.write_text(AGE_KEY_CONTENT)
        assert extract_public_key(key_file) == PUBLIC_KEY

    def test_raises_when_file_missing(self, tmp_path):
        with pytest.raises(KeyError, match="not found"):
            extract_public_key(tmp_path / "missing.txt")

    def test_raises_when_no_public_key_line(self, tmp_path):
        key_file = tmp_path / "key.txt"
        key_file.write_text("AGE-SECRET-KEY-1QQQ\n")
        with pytest.raises(KeyError, match="No public key found"):
            extract_public_key(key_file)


class TestGenerateKeypair:
    def test_generates_keypair_and_returns_public_key(self, tmp_path):
        key_file = tmp_path / "key.txt"
        with patch("envcrypt.keys.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(returncode=0)
            key_file.write_text(AGE_KEY_CONTENT)
            pub = extract_public_key(key_file)
        assert pub == PUBLIC_KEY

    def test_raises_when_key_file_already_exists(self, tmp_path):
        key_file = tmp_path / "key.txt"
        key_file.write_text(AGE_KEY_CONTENT)
        with pytest.raises(KeyError, match="already exists"):
            generate_keypair(key_file)

    def test_raises_when_age_keygen_not_found(self, tmp_path):
        key_file = tmp_path / "key.txt"
        with patch("envcrypt.keys.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(KeyError, match="age-keygen not found"):
                generate_keypair(key_file)

    def test_raises_on_nonzero_exit(self, tmp_path):
        key_file = tmp_path / "key.txt"
        with patch("envcrypt.keys.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(returncode=1, stderr="error")
            with pytest.raises(KeyError, match="Key generation failed"):
                generate_keypair(key_file)
