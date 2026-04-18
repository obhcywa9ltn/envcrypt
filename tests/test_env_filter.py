"""Tests for envcrypt.env_filter."""
from __future__ import annotations

from pathlib import Path

import pytest

from envcrypt.env_filter import FilterError, exclude_keys, filter_by_keys, filter_by_pattern


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# comment\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "API_KEY=secret\n"
        "API_SECRET=topsecret\n"
        "PLAIN=value\n"
    )
    return p


def test_filter_by_keys_returns_requested(env_file: Path) -> None:
    result = filter_by_keys(env_file, ["DB_HOST", "DB_PORT"])
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_filter_by_keys_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FilterError, match="not found"):
        filter_by_keys(tmp_path / "missing.env", ["KEY"])


def test_filter_by_keys_raises_on_missing_key(env_file: Path) -> None:
    with pytest.raises(FilterError, match="keys not found"):
        filter_by_keys(env_file, ["DB_HOST", "NONEXISTENT"])


def test_filter_by_pattern_matches_prefix(env_file: Path) -> None:
    result = filter_by_pattern(env_file, "DB_*")
    assert set(result.keys()) == {"DB_HOST", "DB_PORT"}


def test_filter_by_pattern_returns_empty_when_no_match(env_file: Path) -> None:
    result = filter_by_pattern(env_file, "MISSING_*")
    assert result == {}


def test_filter_by_pattern_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FilterError, match="not found"):
        filter_by_pattern(tmp_path / "missing.env", "*")


def test_exclude_keys_removes_specified(env_file: Path) -> None:
    result = exclude_keys(env_file, ["API_KEY", "API_SECRET"])
    assert "API_KEY" not in result
    assert "API_SECRET" not in result
    assert "DB_HOST" in result


def test_exclude_keys_ignores_unknown_keys(env_file: Path) -> None:
    result = exclude_keys(env_file, ["NONEXISTENT"])
    assert "DB_HOST" in result


def test_exclude_keys_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FilterError, match="not found"):
        exclude_keys(tmp_path / "missing.env", ["KEY"])


def test_parse_ignores_comments_and_blanks(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("# comment\n\nKEY=val\n")
    result = filter_by_keys(p, ["KEY"])
    assert result == {"KEY": "val"}
