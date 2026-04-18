"""Tests for envcrypt.env_validate."""
from pathlib import Path
import pytest

from envcrypt.env_validate import (
    ValidateError,
    ValidationResult,
    validate_env_file,
)


def write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(content)
    return p


def test_raises_when_file_missing(tmp_path):
    with pytest.raises(ValidateError, match="not found"):
        validate_env_file(tmp_path / "missing.env")


def test_ok_for_clean_file(tmp_path):
    p = write(tmp_path, "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    result = validate_env_file(p)
    assert result.ok


def test_ignores_comments_and_blanks(tmp_path):
    p = write(tmp_path, "# comment\n\nFOO=bar\n")
    result = validate_env_file(p)
    assert result.ok


def test_flags_missing_equals(tmp_path):
    p = write(tmp_path, "BADLINE\n")
    result = validate_env_file(p)
    assert not result.ok
    assert any("missing '='" in i.message for i in result.issues)


def test_flags_lowercase_key_when_uppercase_required(tmp_path):
    p = write(tmp_path, "my_key=value\n")
    result = validate_env_file(p, require_uppercase=True)
    assert not result.ok
    assert any("my_key" in i.message for i in result.issues)


def test_allows_lowercase_when_not_required(tmp_path):
    p = write(tmp_path, "my_key=value\n")
    result = validate_env_file(p, require_uppercase=False)
    assert result.ok


def test_flags_empty_value_when_required(tmp_path):
    p = write(tmp_path, "FOO=\n")
    result = validate_env_file(p, require_values=True)
    assert not result.ok
    assert any("no value" in i.message for i in result.issues)


def test_ok_empty_value_when_not_required(tmp_path):
    p = write(tmp_path, "FOO=\n")
    result = validate_env_file(p, require_values=False)
    assert result.ok


def test_flags_missing_required_key(tmp_path):
    p = write(tmp_path, "FOO=bar\n")
    result = validate_env_file(p, required_keys=["DATABASE_URL"])
    assert not result.ok
    assert any("DATABASE_URL" in i.message for i in result.issues)


def test_no_issue_when_required_key_present(tmp_path):
    p = write(tmp_path, "DATABASE_URL=postgres://localhost\n")
    result = validate_env_file(p, required_keys=["DATABASE_URL"])
    assert result.ok


def test_issue_line_number_is_correct(tmp_path):
    p = write(tmp_path, "GOOD=ok\nBAD_line\n")
    result = validate_env_file(p)
    issue = next(i for i in result.issues if "missing '='" in i.message)
    assert issue.line_number == 2
