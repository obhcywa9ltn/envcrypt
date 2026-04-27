"""Tests for envcrypt.env_uppercase."""
from __future__ import annotations

from pathlib import Path

import pytest

from envcrypt.env_uppercase import UppercaseError, list_non_uppercase_keys, uppercase_env_file


@pytest.fixture()
def env_file(tmp_path: Path):
    def _make(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _make


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(UppercaseError, match="not found"):
        list_non_uppercase_keys(tmp_path / "missing.env")


def test_list_empty_for_already_uppercase(env_file) -> None:
    p = env_file("FOO=bar\nBAZ=qux\n")
    assert list_non_uppercase_keys(p) == []


def test_list_detects_lowercase_key(env_file) -> None:
    p = env_file("foo=bar\nBAZ=qux\n")
    issues = list_non_uppercase_keys(p)
    assert issues == ["foo"]


def test_list_ignores_comments_and_blanks(env_file) -> None:
    p = env_file("# comment\n\nFOO=bar\n")
    assert list_non_uppercase_keys(p) == []


def test_list_ignores_lines_without_equals(env_file) -> None:
    p = env_file("NOEQUALS\nFOO=bar\n")
    assert list_non_uppercase_keys(p) == []


def test_uppercase_rewrites_keys_in_place(env_file) -> None:
    p = env_file("foo=bar\nbaz=qux\n")
    target, changed = uppercase_env_file(p)
    assert target == p
    assert changed == 2
    content = p.read_text()
    assert "FOO=bar" in content
    assert "BAZ=qux" in content


def test_uppercase_writes_to_dest(env_file, tmp_path: Path) -> None:
    p = env_file("foo=bar\n")
    dest = tmp_path / "out" / ".env"
    target, changed = uppercase_env_file(p, dest)
    assert target == dest
    assert dest.exists()
    assert "FOO=bar" in dest.read_text()
    assert p.read_text() == "foo=bar\n"  # original untouched


def test_uppercase_preserves_comments_and_blanks(env_file) -> None:
    p = env_file("# header\n\nfoo=bar\n")
    _, changed = uppercase_env_file(p)
    content = p.read_text()
    assert "# header" in content
    assert "\n\n" in content
    assert changed == 1


def test_uppercase_value_with_equals_sign(env_file) -> None:
    p = env_file("db_url=postgres://user:pass@host/db?ssl=true\n")
    _, changed = uppercase_env_file(p)
    content = p.read_text()
    assert "DB_URL=postgres://user:pass@host/db?ssl=true" in content
    assert changed == 1


def test_no_change_returns_zero(env_file) -> None:
    p = env_file("FOO=bar\n")
    _, changed = uppercase_env_file(p)
    assert changed == 0
