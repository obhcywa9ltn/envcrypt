"""Tests for envcrypt.crypto encryption/decryption utilities."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from envcrypt.crypto import (
    AgeEncryptionError,
    check_age_installed,
    encrypt_file,
    decrypt_file,
)


def make_completed_process(returncode=0, stdout="", stderr=""):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


class TestCheckAgeInstalled:
    def test_returns_true_when_age_present(self):
        with patch("subprocess.run", return_value=make_completed_process(0, "age v1.1.1")):
            assert check_age_installed() is True

    def test_returns_false_when_age_missing(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert check_age_installed() is False

    def test_returns_false_on_nonzero_exit(self):
        with patch("subprocess.run", return_value=make_completed_process(1)):
            assert check_age_installed() is False


class TestEncryptFile:
    def test_raises_if_no_recipients(self, tmp_path):
        src = tmp_path / "test.env"
        src.write_text("SECRET=abc")
        with pytest.raises(AgeEncryptionError, match="recipient"):
            encrypt_file(src, tmp_path / "test.env.age", recipients=[])

    def test_calls_age_with_correct_args(self, tmp_path):
        src = tmp_path / "test.env"
        src.write_text("SECRET=abc")
        dst = tmp_path / "test.env.age"
        recipients = ["age1abc123", "age1xyz456"]

        with patch("subprocess.run", return_value=make_completed_process(0)) as mock_run:
            encrypt_file(src, dst, recipients)
            cmd = mock_run.call_args[0][0]
            assert "age" in cmd
            assert "--recipient" in cmd
            assert "age1abc123" in cmd
            assert "age1xyz456" in cmd
            assert str(dst) in cmd

    def test_raises_on_age_failure(self, tmp_path):
        src = tmp_path / "test.env"
        src.write_text("SECRET=abc")
        with patch("subprocess.run", return_value=make_completed_process(1, stderr="bad key")):
            with pytest.raises(AgeEncryptionError, match="bad key"):
                encrypt_file(src, tmp_path / "out.age", recipients=["age1abc"])


class TestDecryptFile:
    def test_calls_age_decrypt_with_correct_args(self, tmp_path):
        src = tmp_path / "test.env.age"
        src.write_bytes(b"encrypted")
        dst = tmp_path / "test.env"
        identity = tmp_path / "key.txt"

        with patch("subprocess.run", return_value=make_completed_process(0)) as mock_run:
            decrypt_file(src, dst, identity)
            cmd = mock_run.call_args[0][0]
            assert "--decrypt" in cmd
            assert "--identity" in cmd
            assert str(identity) in cmd
            assert str(dst) in cmd

    def test_raises_on_decryption_failure(self, tmp_path):
        with patch("subprocess.run", return_value=make_completed_process(1, stderr="no identity")):
            with pytest.raises(AgeEncryptionError, match="no identity"):
                decrypt_file("enc.age", "out.env", "key.txt")
