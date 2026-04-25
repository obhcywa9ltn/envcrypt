"""Tests for envcrypt.env_dedup."""

from pathlib import Path

import pytest

from envcrypt.env_dedup import DedupError, dedup_env_file, find_duplicates


@pytest.fixture()
def env_file(tmp_path: Path):
    """Return a helper that writes content to a temp .env file."""

    def _make(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p

    return _make


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_find_duplicates_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(DedupError, match="File not found"):
        find_duplicates(tmp_path / "missing.env")


def test_find_duplicates_empty_for_clean_file(env_file):
    p = env_file("FOO=1\nBAR=2\n")
    assert find_duplicates(p) == []


def test_find_duplicates_detects_repeated_key(env_file):
    p = env_file("FOO=1\nBAR=2\nFOO=3\n")
    dupes = dict(find_duplicates(p))
    assert "FOO" in dupes
    assert dupes["FOO"] == [1, 3]


def test_find_duplicates_ignores_comments_and_blanks(env_file):
    p = env_file("# comment\n\nFOO=1\nFOO=2\n")
    dupes = dict(find_duplicates(p))
    assert "FOO" in dupes
    assert len(dupes) == 1


# ---------------------------------------------------------------------------
# dedup_env_file
# ---------------------------------------------------------------------------

def test_dedup_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(DedupError, match="File not found"):
        dedup_env_file(tmp_path / "missing.env")


def test_dedup_raises_on_invalid_keep(env_file):
    p = env_file("FOO=1\n")
    with pytest.raises(DedupError, match="keep must be"):
        dedup_env_file(p, keep="middle")


def test_dedup_returns_zero_when_no_duplicates(env_file):
    p = env_file("FOO=1\nBAR=2\n")
    removed = dedup_env_file(p)
    assert removed == 0


def test_dedup_keep_last_removes_earlier_occurrence(env_file):
    p = env_file("FOO=first\nBAR=2\nFOO=last\n")
    removed = dedup_env_file(p, keep="last")
    assert removed == 1
    lines = p.read_text().splitlines()
    assert "FOO=last" in lines
    assert "FOO=first" not in lines


def test_dedup_keep_first_removes_later_occurrence(env_file):
    p = env_file("FOO=first\nBAR=2\nFOO=last\n")
    removed = dedup_env_file(p, keep="first")
    assert removed == 1
    lines = p.read_text().splitlines()
    assert "FOO=first" in lines
    assert "FOO=last" not in lines


def test_dedup_writes_to_dest(env_file, tmp_path: Path):
    p = env_file("FOO=1\nFOO=2\n")
    dest = tmp_path / "out" / ".env"
    dedup_env_file(p, dest=dest)
    assert dest.exists()
    assert p.read_text() == "FOO=1\nFOO=2\n"  # original untouched


def test_dedup_preserves_comments_and_blanks(env_file):
    content = "# header\n\nFOO=1\nBAR=2\nFOO=3\n"
    p = env_file(content)
    dedup_env_file(p, keep="last")
    result = p.read_text()
    assert "# header" in result
    assert result.count("\n\n") >= 1  # blank line preserved
