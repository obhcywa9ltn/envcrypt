"""Tests for envcrypt.env_patch."""
from __future__ import annotations

from pathlib import Path

import pytest

from envcrypt.env_patch import PatchError, patch_env_file, list_patch_keys


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n# a comment\n\nSECRET=hunter2\n")
    return p


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(PatchError, match="not found"):
        patch_env_file(tmp_path / "missing.env", updates={"A": "1"})


def test_updates_existing_key(env_file: Path) -> None:
    added_updated, removed = patch_env_file(env_file, updates={"FOO": "newval"})
    assert added_updated == 1
    assert removed == 0
    contents = env_file.read_text()
    assert "FOO=newval" in contents
    assert "FOO=bar" not in contents


def test_adds_new_key(env_file: Path) -> None:
    added_updated, removed = patch_env_file(env_file, updates={"NEWKEY": "42"})
    assert added_updated == 1
    assert removed == 0
    assert "NEWKEY=42" in env_file.read_text()


def test_removes_existing_key(env_file: Path) -> None:
    added_updated, removed = patch_env_file(env_file, removals=["BAZ"])
    assert removed == 1
    assert "BAZ" not in env_file.read_text()


def test_removes_nonexistent_key_is_noop(env_file: Path) -> None:
    _, removed = patch_env_file(env_file, removals=["DOES_NOT_EXIST"])
    assert removed == 0


def test_combined_update_and_remove(env_file: Path) -> None:
    added_updated, removed = patch_env_file(
        env_file, updates={"FOO": "updated", "EXTRA": "yes"}, removals=["SECRET"]
    )
    text = env_file.read_text()
    assert "FOO=updated" in text
    assert "EXTRA=yes" in text
    assert "SECRET" not in text
    assert added_updated == 2
    assert removed == 1


def test_writes_to_dest(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out" / ".env.patched"
    patch_env_file(env_file, updates={"FOO": "destval"}, dest=dest)
    assert dest.exists()
    assert "FOO=destval" in dest.read_text()
    # original unchanged
    assert "FOO=bar" in env_file.read_text()


def test_preserves_comments_and_blank_lines(env_file: Path) -> None:
    patch_env_file(env_file, updates={"FOO": "x"})
    text = env_file.read_text()
    assert "# a comment" in text
    assert "\n\n" in text


def test_list_patch_keys_returns_sorted(env_file: Path) -> None:
    keys = list_patch_keys(env_file)
    assert keys == sorted(keys)
    assert "FOO" in keys
    assert "BAZ" in keys


def test_list_patch_keys_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(PatchError, match="not found"):
        list_patch_keys(tmp_path / "nope.env")
