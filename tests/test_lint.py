"""Tests for envcrypt.lint."""
from pathlib import Path
import pytest
from envcrypt.lint import LintError, lint_env_file


def write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(content)
    return p


def test_raises_when_file_missing(tmp_path):
    with pytest.raises(LintError):
        lint_env_file(tmp_path / "missing.env")


def test_ok_for_clean_file(tmp_path):
    p = write(tmp_path, "KEY=value\nOTHER=123\n")
    result = lint_env_file(p)
    assert result.ok
    assert result.issues == []


def test_ignores_comments_and_blanks(tmp_path):
    p = write(tmp_path, "# comment\n\nKEY=val\n")
    result = lint_env_file(p)
    assert result.ok


def test_flags_missing_equals(tmp_path):
    p = write(tmp_path, "BADLINE\n")
    result = lint_env_file(p)
    assert not result.ok
    assert any("Missing '='" in i.message for i in result.issues)


def test_flags_duplicate_key(tmp_path):
    p = write(tmp_path, "KEY=a\nKEY=b\n")
    result = lint_env_file(p)
    assert not result.ok
    assert any("Duplicate key" in i.message for i in result.issues)


def test_flags_key_with_whitespace(tmp_path):
    p = write(tmp_path, "BAD KEY=value\n")
    result = lint_env_file(p)
    assert not result.ok
    assert any("whitespace" in i.message for i in result.issues)


def test_flags_empty_key(tmp_path):
    p = write(tmp_path, "=value\n")
    result = lint_env_file(p)
    assert not result.ok
    assert any("Empty key" in i.message for i in result.issues)


def test_flags_unclosed_quote(tmp_path):
    p = write(tmp_path, 'KEY="unclosed\n')
    result = lint_env_file(p)
    assert not result.ok
    assert any("Unclosed quote" in i.message for i in result.issues)


def test_issue_line_numbers(tmp_path):
    p = write(tmp_path, "GOOD=ok\nBADLINE\n")
    result = lint_env_file(p)
    assert result.issues[0].line == 2
