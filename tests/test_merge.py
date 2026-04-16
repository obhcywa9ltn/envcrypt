"""Tests for envcrypt.merge."""
from pathlib import Path

import pytest

from envcrypt.merge import (
    ConflictStrategy,
    MergeError,
    merge_env_files,
)


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_raises_when_base_missing(tmp_path):
    theirs = write(tmp_path / "theirs.env", "A=1\n")
    with pytest.raises(MergeError, match="Base file not found"):
        merge_env_files(tmp_path / "missing.env", theirs)


def test_raises_when_incoming_missing(tmp_path):
    ours = write(tmp_path / "ours.env", "A=1\n")
    with pytest.raises(MergeError, match="Incoming file not found"):
        merge_env_files(ours, tmp_path / "missing.env")


def test_merges_disjoint_keys(tmp_path):
    ours = write(tmp_path / "ours.env", "A=1\nB=2\n")
    theirs = write(tmp_path / "theirs.env", "C=3\n")
    result = merge_env_files(ours, theirs)
    assert result.merged == {"A": "1", "B": "2", "C": "3"}
    assert result.conflicts == []


def test_raises_on_conflict_with_error_strategy(tmp_path):
    ours = write(tmp_path / "ours.env", "A=1\n")
    theirs = write(tmp_path / "theirs.env", "A=2\n")
    with pytest.raises(MergeError, match="Conflict on key 'A'"):
        merge_env_files(ours, theirs, strategy=ConflictStrategy.ERROR)


def test_ours_strategy_keeps_base_value(tmp_path):
    ours = write(tmp_path / "ours.env", "A=1\n")
    theirs = write(tmp_path / "theirs.env", "A=2\n")
    result = merge_env_files(ours, theirs, strategy=ConflictStrategy.OURS)
    assert result.merged["A"] == "1"
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "A"


def test_theirs_strategy_uses_incoming_value(tmp_path):
    ours = write(tmp_path / "ours.env", "A=1\n")
    theirs = write(tmp_path / "theirs.env", "A=2\n")
    result = merge_env_files(ours, theirs, strategy=ConflictStrategy.THEIRS)
    assert result.merged["A"] == "2"


def test_writes_dest_file(tmp_path):
    ours = write(tmp_path / "ours.env", "A=1\n")
    theirs = write(tmp_path / "theirs.env", "B=2\n")
    dest = tmp_path / "out" / "merged.env"
    merge_env_files(ours, theirs, dest=dest)
    assert dest.exists()
    content = dest.read_text()
    assert "A=1" in content
    assert "B=2" in content


def test_ignores_comments_and_blank_lines(tmp_path):
    ours = write(tmp_path / "ours.env", "# comment\n\nA=1\n")
    theirs = write(tmp_path / "theirs.env", "# another\nB=2\n")
    result = merge_env_files(ours, theirs)
    assert set(result.merged.keys()) == {"A", "B"}


def test_identical_values_not_flagged_as_conflict(tmp_path):
    ours = write(tmp_path / "ours.env", "A=same\n")
    theirs = write(tmp_path / "theirs.env", "A=same\n")
    result = merge_env_files(ours, theirs, strategy=ConflictStrategy.ERROR)
    assert result.conflicts == []
    assert result.merged["A"] == "same"
