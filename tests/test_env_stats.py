"""Tests for envcrypt.env_stats."""
from pathlib import Path

import pytest

from envcrypt.env_stats import EnvStats, StatsError, env_stats, summary_text


@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _write


def test_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(StatsError, match="not found"):
        env_stats(tmp_path / "missing.env")


def test_counts_keys(env_file):
    p = env_file("FOO=bar\nBAZ=qux\n")
    s = env_stats(p)
    assert s.key_count == 2


def test_counts_blank_lines(env_file):
    p = env_file("FOO=bar\n\nBAZ=qux\n")
    s = env_stats(p)
    assert s.blank_lines == 1


def test_counts_comment_lines(env_file):
    p = env_file("# comment\nFOO=bar\n")
    s = env_stats(p)
    assert s.comment_lines == 1
    assert s.key_count == 1


def test_counts_empty_values(env_file):
    p = env_file("FOO=\nBAR=hello\n")
    s = env_stats(p)
    assert s.empty_values == 1
    assert s.defined_keys == 1


def test_detects_duplicate_keys(env_file):
    p = env_file("FOO=a\nFOO=b\nBAR=c\n")
    s = env_stats(p)
    assert "FOO" in s.duplicate_keys
    assert "BAR" not in s.duplicate_keys


def test_no_duplicates_in_clean_file(env_file):
    p = env_file("A=1\nB=2\n")
    s = env_stats(p)
    assert s.duplicate_keys == []


def test_total_lines(env_file):
    p = env_file("A=1\n\n# x\nB=2\n")
    s = env_stats(p)
    assert s.total_lines == 4


def test_summary_text_contains_key_count(env_file):
    p = env_file("A=1\nB=\n")
    s = env_stats(p)
    text = summary_text(s)
    assert "Keys defined" in text
    assert "2" in text


def test_summary_text_shows_duplicates(env_file):
    p = env_file("X=1\nX=2\n")
    s = env_stats(p)
    text = summary_text(s)
    assert "X" in text


def test_summary_text_shows_none_when_no_duplicates(env_file):
    p = env_file("A=1\n")
    s = env_stats(p)
    assert "none" in summary_text(s)
