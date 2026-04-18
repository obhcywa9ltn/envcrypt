"""Tests for envcrypt.env_sort."""
import pytest
from pathlib import Path

from envcrypt.env_sort import SortError, sort_env_file, sorted_keys


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("ZEBRA=1\nAPPLE=2\nMANGO=3\n")
    return p


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(SortError, match="not found"):
        sort_env_file(tmp_path / "missing.env")


def test_sorts_keys_alphabetically(env_file: Path) -> None:
    sort_env_file(env_file)
    lines = [l for l in env_file.read_text().splitlines() if l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_reverse_sort(env_file: Path) -> None:
    sort_env_file(env_file, reverse=True)
    lines = [l for l in env_file.read_text().splitlines() if l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys, reverse=True)


def test_writes_to_dest(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out" / "sorted.env"
    result = sort_env_file(env_file, dest=dest)
    assert result == dest
    assert dest.exists()


def test_preserves_header_comments(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("# header\n\nZEBRA=1\nAPPLE=2\n")
    sort_env_file(p)
    content = p.read_text()
    assert content.startswith("# header")


def test_sorted_keys_returns_list(env_file: Path) -> None:
    keys = sorted_keys(env_file)
    assert keys == ["APPLE", "MANGO", "ZEBRA"]


def test_sorted_keys_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(SortError):
        sorted_keys(tmp_path / "nope.env")


def test_sorted_keys_ignores_comments(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("# comment\nBETA=2\nALPHA=1\n")
    assert sorted_keys(p) == ["ALPHA", "BETA"]
