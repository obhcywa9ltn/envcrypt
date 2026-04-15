"""Tests for envcrypt.verify."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envcrypt.verify import verify_env_file, VerifyError, VerifyResult
from envcrypt.crypto import AgeEncryptionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ENV_CONTENT = b"KEY=value\nSECRET=hunter2\n"


def _write(path: Path, content: bytes = ENV_CONTENT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


# ---------------------------------------------------------------------------
# verify_env_file
# ---------------------------------------------------------------------------

class TestVerifyEnvFile:
    def test_raises_when_env_file_missing(self, tmp_path):
        env_file = tmp_path / ".env"
        key_file = tmp_path / "key.txt"
        with pytest.raises(VerifyError, match="env file not found"):
            verify_env_file(env_file, key_file, base=tmp_path)

    def test_returns_no_match_when_encrypted_missing(self, tmp_path):
        env_file = _write(tmp_path / ".env")
        key_file = tmp_path / "key.txt"
        result = verify_env_file(env_file, key_file, base=tmp_path)
        assert isinstance(result, VerifyResult)
        assert result.match is False
        assert "does not exist" in (result.reason or "")

    def test_returns_no_match_on_decryption_failure(self, tmp_path):
        env_file = _write(tmp_path / ".env")
        key_file = _write(tmp_path / "key.txt", b"fake-key")
        encrypted_file = _write(tmp_path / ".envcrypt" / ".env.age", b"garbage")

        with patch("envcrypt.verify.get_encrypted_path", return_value=encrypted_file), \
             patch("envcrypt.verify.decrypt_file", side_effect=AgeEncryptionError("bad")):
            result = verify_env_file(env_file, key_file, base=tmp_path)

        assert result.match is False
        assert "decryption failed" in (result.reason or "")

    def test_returns_match_false_when_content_differs(self, tmp_path):
        env_file = _write(tmp_path / ".env", b"KEY=original\n")
        key_file = _write(tmp_path / "key.txt", b"fake-key")
        encrypted_file = _write(tmp_path / ".envcrypt" / ".env.age", b"encrypted")

        def fake_decrypt(src, dest, key):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"KEY=different\n")

        with patch("envcrypt.verify.get_encrypted_path", return_value=encrypted_file), \
             patch("envcrypt.verify.decrypt_file", side_effect=fake_decrypt):
            result = verify_env_file(env_file, key_file, base=tmp_path)

        assert result.match is False
        assert result.reason == "content differs"

    def test_returns_match_true_when_content_identical(self, tmp_path):
        env_file = _write(tmp_path / ".env", ENV_CONTENT)
        key_file = _write(tmp_path / "key.txt", b"fake-key")
        encrypted_file = _write(tmp_path / ".envcrypt" / ".env.age", b"encrypted")

        def fake_decrypt(src, dest, key):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(ENV_CONTENT)

        with patch("envcrypt.verify.get_encrypted_path", return_value=encrypted_file), \
             patch("envcrypt.verify.decrypt_file", side_effect=fake_decrypt):
            result = verify_env_file(env_file, key_file, base=tmp_path)

        assert result.match is True
        assert result.reason is None

    def test_result_exposes_both_paths(self, tmp_path):
        env_file = _write(tmp_path / ".env")
        key_file = tmp_path / "key.txt"
        result = verify_env_file(env_file, key_file, base=tmp_path)
        assert result.env_file == env_file
        assert result.encrypted_file is not None
