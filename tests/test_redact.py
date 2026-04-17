"""Tests for envcrypt.redact."""

from pathlib import Path
import pytest

from envcrypt.redact import (
    RedactError,
    REDACT_PLACEHOLDER,
    is_sensitive,
    redact_dict,
    redact_file,
)


# --- is_sensitive ---

def test_password_is_sensitive():
    assert is_sensitive("DB_PASSWORD") is True

def test_token_is_sensitive():
    assert is_sensitive("GITHUB_TOKEN") is True

def test_plain_key_not_sensitive():
    assert is_sensitive("APP_NAME") is False

def test_api_key_is_sensitive():
    assert is_sensitive("STRIPE_API_KEY") is True


# --- redact_dict ---

def test_redacts_sensitive_keys():
    env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
    result = redact_dict(env)
    assert result["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result["APP_NAME"] == "myapp"

def test_redacts_explicit_keys():
    env = {"APP_NAME": "myapp", "REGION": "us-east-1"}
    result = redact_dict(env, keys=["REGION"])
    assert result["REGION"] == REDACT_PLACEHOLDER
    assert result["APP_NAME"] == "myapp"

def test_does_not_mutate_original():
    env = {"DB_PASSWORD": "s3cr3t"}
    redact_dict(env)
    assert env["DB_PASSWORD"] == "s3cr3t"


# --- redact_file ---

def write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return p


def test_raises_when_source_missing(tmp_path):
    with pytest.raises(RedactError):
        redact_file(tmp_path / "missing.env", tmp_path / "out.env")


def test_redacts_sensitive_lines(tmp_path):
    src = write(tmp_path, ".env", "APP_NAME=myapp\nDB_PASSWORD=secret\n")
    dest = tmp_path / "out.env"
    count = redact_file(src, dest)
    assert count == 1
    content = dest.read_text()
    assert f"DB_PASSWORD={REDACT_PLACEHOLDER}" in content
    assert "APP_NAME=myapp" in content


def test_preserves_comments_and_blanks(tmp_path):
    src = write(tmp_path, ".env", "# comment\n\nAPP=x\n")
    dest = tmp_path / "out.env"
    redact_file(src, dest)
    content = dest.read_text()
    assert "# comment" in content


def test_redacts_explicit_keys_in_file(tmp_path):
    src = write(tmp_path, ".env", "REGION=us-east-1\nAPP=x\n")
    dest = tmp_path / "out.env"
    count = redact_file(src, dest, keys=["REGION"])
    assert count == 1
    assert f"REGION={REDACT_PLACEHOLDER}" in dest.read_text()


def test_creates_dest_parent_dirs(tmp_path):
    src = write(tmp_path, ".env", "X=1\n")
    dest = tmp_path / "sub" / "dir" / "out.env"
    redact_file(src, dest)
    assert dest.exists()
