"""Tests for envcrypt.env_rename."""
from __future__ import annotations

from pathlib import Path

import pytest

from envcrypt.env_rename import RenameError, list_keys, rename_key


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n# comment\nEMPTY=\n")
    return p


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(RenameError, match="not found"):
        rename_key(tmp_path / "missing.env", "FOO", "BAR")


def test_raises_when_old_key_missing(env_file: Path) -> None:
    with pytest.raises(RenameError, match="Key not found"):
        rename_key(env_file, "NOPE", "NEW")


def test_raises_when_new_key_already_exists(env_file: Path) -> None:
    with pytest.raises(RenameError, match="already exists"):
        rename_key(env_file, "FOO", "BAZ")


def test_renames_key_in_place(env_file: Path) -> None:
    rename_key(env_file, "FOO", "FOO_NEW")
    content = env_file.read_text()
    assert "FOO_NEW=bar" in content
    assert "FOO=" not in content


def test_renames_to_dest(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out" / ".env"
    rename_key(env_file, "FOO", "FOO2", dest)
    assert dest.exists()
    assert "FOO2=bar" in dest.read_text()
    # original unchanged
    assert "FOO=bar" in env_file.read_text()


def test_preserves_comments_and_blank_lines(env_file: Path) -> None:
    rename_key(env_file, "BAZ", "BAZ_RENAMED")
    content = env_file.read_text()
    assert "# comment" in content
    assert "EMPTY=" in content


def test_list_keys_returns_all_keys(env_file: Path) -> None:
    keys = list_keys(env_file)
    assert keys == ["FOO", "BAZ", "EMPTY"]


def test_list_keys_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(RenameError, match="not found"):
        list_keys(tmp_path / "missing.env")


def test_list_keys_empty_file(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("# only comments\n\n")
    assert list_keys(p) == []
