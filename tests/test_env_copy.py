"""Tests for envcrypt.env_copy."""
from pathlib import Path

import pytest

from envcrypt.env_copy import CopyError, copy_all, copy_keys


@pytest.fixture()
def env_files(tmp_path: Path):
    src = tmp_path / ".env.src"
    dest = tmp_path / ".env.dest"
    src.write_text("FOO=bar\nBAZ=qux\nSECRET=s3cr3t\n")
    dest.write_text("EXISTING=yes\n")
    return src, dest


def test_raises_when_src_missing(tmp_path: Path):
    src = tmp_path / ".env.missing"
    dest = tmp_path / ".env.dest"
    dest.write_text("")
    with pytest.raises(CopyError, match="Source file not found"):
        copy_keys(src, dest, ["FOO"])


def test_raises_when_dest_missing(tmp_path: Path):
    src = tmp_path / ".env.src"
    src.write_text("FOO=bar\n")
    dest = tmp_path / ".env.dest"
    with pytest.raises(CopyError, match="Destination file not found"):
        copy_keys(src, dest, ["FOO"])


def test_raises_when_key_missing_in_src(env_files):
    src, dest = env_files
    with pytest.raises(CopyError, match="Keys not found in source"):
        copy_keys(src, dest, ["NOPE"])


def test_raises_on_conflict_without_overwrite(tmp_path: Path):
    src = tmp_path / ".env.src"
    dest = tmp_path / ".env.dest"
    src.write_text("FOO=bar\n")
    dest.write_text("FOO=old\n")
    with pytest.raises(CopyError, match="already exist"):
        copy_keys(src, dest, ["FOO"])


def test_copies_key_to_dest(env_files):
    src, dest = env_files
    copied = copy_keys(src, dest, ["FOO"])
    assert copied == ["FOO"]
    content = dest.read_text()
    assert "FOO=bar" in content
    assert "EXISTING=yes" in content


def test_overwrite_replaces_existing(tmp_path: Path):
    src = tmp_path / ".env.src"
    dest = tmp_path / ".env.dest"
    src.write_text("FOO=newval\n")
    dest.write_text("FOO=oldval\nOTHER=x\n")
    copy_keys(src, dest, ["FOO"], overwrite=True)
    lines = dest.read_text().splitlines()
    assert "FOO=newval" in lines
    assert "FOO=oldval" not in lines


def test_copy_all_copies_every_key(env_files):
    src, dest = env_files
    copied = copy_all(src, dest)
    assert set(copied) == {"FOO", "BAZ", "SECRET"}
    content = dest.read_text()
    assert "BAZ=qux" in content
    assert "SECRET=s3cr3t" in content


def test_copy_all_raises_when_src_missing(tmp_path: Path):
    src = tmp_path / ".env.missing"
    dest = tmp_path / ".env.dest"
    dest.write_text("")
    with pytest.raises(CopyError, match="Source file not found"):
        copy_all(src, dest)
