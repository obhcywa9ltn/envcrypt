"""Tests for envcrypt.env_flatten."""
from __future__ import annotations

from pathlib import Path

import pytest

from envcrypt.env_flatten import FlattenError, flatten_prefixes, list_prefixes


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "AWS_KEY=abc123\n"
        "AWS_SECRET=xyz\n"
        "PLAIN=value\n"
        "# a comment\n"
        "\n"
        "APP_NAME=myapp\n"
    )
    return p


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FlattenError, match="not found"):
        flatten_prefixes(tmp_path / "missing.env", ["DB"])


def test_raises_when_no_prefixes(env_file: Path) -> None:
    with pytest.raises(FlattenError, match="at least one prefix"):
        flatten_prefixes(env_file, [])


def test_returns_only_matching_prefix(env_file: Path) -> None:
    result = flatten_prefixes(env_file, ["DB"])
    assert set(result.keys()) == {"DB_HOST", "DB_PORT"}
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"


def test_multiple_prefixes(env_file: Path) -> None:
    result = flatten_prefixes(env_file, ["DB", "AWS"])
    assert "DB_HOST" in result
    assert "AWS_KEY" in result
    assert "PLAIN" not in result


def test_strip_prefix_removes_token(env_file: Path) -> None:
    result = flatten_prefixes(env_file, ["DB"], strip_prefix=True)
    assert "HOST" in result
    assert "PORT" in result
    assert result["HOST"] == "localhost"


def test_strip_prefix_false_keeps_full_key(env_file: Path) -> None:
    result = flatten_prefixes(env_file, ["DB"], strip_prefix=False)
    assert "DB_HOST" in result
    assert "HOST" not in result


def test_writes_dest_file(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out" / "db.env"
    flatten_prefixes(env_file, ["DB"], dest=dest)
    assert dest.exists()
    content = dest.read_text()
    assert "DB_HOST=localhost" in content
    assert "AWS_KEY" not in content


def test_list_prefixes_returns_unique(env_file: Path) -> None:
    prefixes = list_prefixes(env_file)
    assert "DB" in prefixes
    assert "AWS" in prefixes
    assert "APP" in prefixes


def test_list_prefixes_excludes_no_separator(env_file: Path) -> None:
    prefixes = list_prefixes(env_file)
    assert "PLAIN" not in prefixes


def test_list_prefixes_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FlattenError, match="not found"):
        list_prefixes(tmp_path / "ghost.env")


def test_no_match_returns_empty_dict(env_file: Path) -> None:
    result = flatten_prefixes(env_file, ["NONEXISTENT"])
    assert result == {}
