"""Tests for envcrypt.rotate module."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from envcrypt.rotate import RotationError, rotate_key, generate_and_rotate


RECIPIENTS_DATA = {"alice": "age1alice000"}


@pytest.fixture
def tmp_key_files(tmp_path):
    old_key = tmp_path / "old.txt"
    new_key = tmp_path / "new.txt"
    old_key.write_text("AGE-SECRET-KEY-OLD")
    new_key.write_text("AGE-SECRET-KEY-NEW")
    return str(old_key), str(new_key)


@pytest.fixture
def recipients_file(tmp_path):
    rf = tmp_path / "recipients.json"
    rf.write_text(json.dumps(RECIPIENTS_DATA))
    return str(rf)


class TestRotateKey:
    def test_raises_when_old_key_missing(self, tmp_path, recipients_file):
        with pytest.raises(RotationError, match="Old private key not found"):
            rotate_key("/nonexistent/old.txt", str(tmp_path / "new.txt"), recipients_file)

    def test_raises_when_new_key_missing(self, tmp_path, recipients_file):
        old_key = tmp_path / "old.txt"
        old_key.write_text("key")
        with pytest.raises(RotationError, match="New private key not found"):
            rotate_key(str(old_key), "/nonexistent/new.txt", recipients_file)

    def test_raises_when_extract_public_key_fails(self, tmp_key_files, recipients_file):
        old_key, new_key = tmp_key_files
        with patch("envcrypt.rotate.extract_public_key", side_effect=Exception("bad key")):
            with pytest.raises(RotationError, match="Failed to extract public key"):
                rotate_key(old_key, new_key, recipients_file)

    def test_raises_when_recipients_load_fails(self, tmp_key_files, tmp_path):
        old_key, new_key = tmp_key_files
        bad_rf = str(tmp_path / "bad.json")
        open(bad_rf, "w").write("not-json")
        with patch("envcrypt.rotate.extract_public_key", return_value="age1new"):
            with pytest.raises(RotationError, match="Failed to load recipients"):
                rotate_key(old_key, new_key, bad_rf)

    def test_skips_missing_vault_files(self, tmp_key_files, recipients_file, tmp_path):
        old_key, new_key = tmp_key_files
        with patch("envcrypt.rotate.extract_public_key", return_value="age1new"), \
             patch("envcrypt.rotate.load_recipients", return_value=RECIPIENTS_DATA), \
             patch("envcrypt.rotate.get_encrypted_path", return_value="/nonexistent/path.age"), \
             patch("envcrypt.rotate.append_audit_entry"):
            result = rotate_key(old_key, new_key, recipients_file)
        assert result == {}

    def test_returns_mapping_on_success(self, tmp_key_files, recipients_file, tmp_path):
        old_key, new_key = tmp_key_files
        fake_encrypted = str(tmp_path / "alice.age")
        open(fake_encrypted, "w").write("encrypted")
        new_encrypted = str(tmp_path / "alice_new.age")

        with patch("envcrypt.rotate.extract_public_key", return_value="age1new"), \
             patch("envcrypt.rotate.load_recipients", return_value=RECIPIENTS_DATA), \
             patch("envcrypt.rotate.get_encrypted_path", return_value=fake_encrypted), \
             patch("envcrypt.rotate.unlock"), \
             patch("envcrypt.rotate.lock", return_value=new_encrypted), \
             patch("envcrypt.rotate.append_audit_entry"):
            result = rotate_key(old_key, new_key, recipients_file)

        assert result == {"alice": new_encrypted}


class TestGenerateAndRotate:
    def test_raises_when_generate_fails(self, tmp_path, recipients_file):
        with patch("envcrypt.rotate.generate_keypair", side_effect=Exception("fail")):
            with pytest.raises(RotationError, match="Failed to generate new keypair"):
                generate_and_rotate(str(tmp_path / "new.txt"), recipients_file)

    def test_returns_public_key_and_path(self, tmp_path, recipients_file):
        new_key_path = str(tmp_path / "new.txt")
        with patch("envcrypt.rotate.generate_keypair", return_value=("age1pub", new_key_path)):
            pub, path = generate_and_rotate(new_key_path, recipients_file)
        assert pub == "age1pub"
        assert path == new_key_path
