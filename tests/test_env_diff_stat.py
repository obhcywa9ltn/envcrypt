"""Tests for envcrypt.env_diff_stat."""
from pathlib import Path
import pytest

from envcrypt.env_diff_stat import DiffStat, DiffStatError, diff_stat


def write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_raises_when_base_missing(tmp_path):
    incoming = write(tmp_path, "incoming.env", "A=1\n")
    with pytest.raises(DiffStatError, match="Base file not found"):
        diff_stat(tmp_path / "missing.env", incoming)


def test_raises_when_incoming_missing(tmp_path):
    base = write(tmp_path, "base.env", "A=1\n")
    with pytest.raises(DiffStatError, match="Incoming file not found"):
        diff_stat(base, tmp_path / "missing.env")


def test_identical_files_are_clean(tmp_path):
    content = "A=1\nB=2\n"
    base = write(tmp_path, "base.env", content)
    incoming = write(tmp_path, "incoming.env", content)
    stat = diff_stat(base, incoming)
    assert stat.is_clean
    assert stat.unchanged == ["A", "B"]


def test_detects_added_key(tmp_path):
    base = write(tmp_path, "base.env", "A=1\n")
    incoming = write(tmp_path, "incoming.env", "A=1\nB=2\n")
    stat = diff_stat(base, incoming)
    assert stat.added == ["B"]
    assert stat.removed == []
    assert stat.changed == []


def test_detects_removed_key(tmp_path):
    base = write(tmp_path, "base.env", "A=1\nB=2\n")
    incoming = write(tmp_path, "incoming.env", "A=1\n")
    stat = diff_stat(base, incoming)
    assert stat.removed == ["B"]
    assert stat.added == []


def test_detects_changed_value(tmp_path):
    base = write(tmp_path, "base.env", "A=old\n")
    incoming = write(tmp_path, "incoming.env", "A=new\n")
    stat = diff_stat(base, incoming)
    assert stat.changed == ["A"]
    assert stat.total_changes == 1


def test_ignores_comments_and_blanks(tmp_path):
    base = write(tmp_path, "base.env", "# comment\n\nA=1\n")
    incoming = write(tmp_path, "incoming.env", "A=1\n")
    stat = diff_stat(base, incoming)
    assert stat.is_clean


def test_total_changes_sums_all(tmp_path):
    base = write(tmp_path, "base.env", "A=1\nB=old\nC=3\n")
    incoming = write(tmp_path, "incoming.env", "B=new\nC=3\nD=4\n")
    stat = diff_stat(base, incoming)
    assert "A" in stat.removed
    assert "B" in stat.changed
    assert "D" in stat.added
    assert stat.total_changes == 3


def test_value_with_equals_sign(tmp_path):
    base = write(tmp_path, "base.env", "URL=http://x.com/a=b\n")
    incoming = write(tmp_path, "incoming.env", "URL=http://x.com/a=b\n")
    stat = diff_stat(base, incoming)
    assert stat.is_clean
