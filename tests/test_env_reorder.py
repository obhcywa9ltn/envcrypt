"""Tests for envcrypt.env_reorder."""

from __future__ import annotations

import pytest
from pathlib import Path

from envcrypt.env_reorder import ReorderError, reorder_env_file, list_keys


@pytest.fixture()
def env_file(tmp_path: Path):
    """Return a factory that writes a .env file and returns its path."""
    def _make(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _make


def test_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(ReorderError, match="File not found"):
        reorder_env_file(tmp_path / "missing.env", tmp_path / "out.env", alphabetical=True)


def test_raises_without_order_or_alphabetical(env_file, tmp_path: Path):
    src = env_file("A=1\nB=2\n")
    with pytest.raises(ReorderError, match="alphabetical"):
        reorder_env_file(src, tmp_path / "out.env")


def test_alphabetical_sort(env_file, tmp_path: Path):
    src = env_file("ZEBRA=1\nAPPLE=2\nMango=3\n")
    dest = tmp_path / "out.env"
    result = reorder_env_file(src, dest, alphabetical=True)
    assert result == ["APPLE", "MANGO", "ZEBRA"] or result == sorted(result)
    text = dest.read_text()
    assert text.index("APPLE") < text.index("ZEBRA")


def test_alphabetical_reverse_sort(env_file, tmp_path: Path):
    src = env_file("APPLE=1\nZEBRA=2\n")
    dest = tmp_path / "out.env"
    result = reorder_env_file(src, dest, alphabetical=True, reverse=True)
    assert result[0] == "ZEBRA"
    assert result[-1] == "APPLE"


def test_explicit_order_puts_keys_first(env_file, tmp_path: Path):
    src = env_file("A=1\nB=2\nC=3\n")
    dest = tmp_path / "out.env"
    result = reorder_env_file(src, dest, order=["C", "A"])
    assert result[0] == "C"
    assert result[1] == "A"
    assert "B" in result


def test_explicit_order_unknown_key_raises(env_file, tmp_path: Path):
    src = env_file("A=1\nB=2\n")
    dest = tmp_path / "out.env"
    with pytest.raises(ReorderError, match="Unknown keys"):
        reorder_env_file(src, dest, order=["A", "MISSING"])


def test_creates_dest_parent_directory(env_file, tmp_path: Path):
    src = env_file("X=1\n")
    dest = tmp_path / "sub" / "dir" / "out.env"
    reorder_env_file(src, dest, alphabetical=True)
    assert dest.exists()


def test_list_keys_returns_current_order(env_file):
    src = env_file("FOO=1\nBAR=2\nBAZ=3\n")
    keys = list_keys(src)
    assert keys == ["FOO", "BAR", "BAZ"]


def test_list_keys_raises_when_missing(tmp_path: Path):
    with pytest.raises(ReorderError, match="File not found"):
        list_keys(tmp_path / "nope.env")


def test_comments_and_blanks_preserved_as_header(env_file, tmp_path: Path):
    src = env_file("# header comment\n\nB=2\nA=1\n")
    dest = tmp_path / "out.env"
    reorder_env_file(src, dest, alphabetical=True)
    text = dest.read_text()
    assert text.startswith("# header comment")


def test_empty_file_writes_unchanged(env_file, tmp_path: Path):
    src = env_file("# just a comment\n")
    dest = tmp_path / "out.env"
    result = reorder_env_file(src, dest, alphabetical=True)
    assert result == []
    assert dest.exists()
