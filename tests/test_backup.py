"""Tests for envcrypt.backup."""
import time
from pathlib import Path

import pytest

from envcrypt.backup import (
    BackupError,
    create_backup,
    get_backup_dir,
    list_backups,
    prune_backups,
    restore_backup,
)


def test_get_backup_dir_defaults_to_cwd(tmp_path):
    result = get_backup_dir(tmp_path)
    assert result == tmp_path / ".envcrypt" / "backups"


def test_create_backup_raises_when_file_missing(tmp_path):
    with pytest.raises(BackupError, match="not found"):
        create_backup(tmp_path / "missing.age", base_dir=tmp_path)


def test_create_backup_copies_file(tmp_path):
    src = tmp_path / "dev.env.age"
    src.write_bytes(b"encrypted")
    dest = create_backup(src, base_dir=tmp_path)
    assert dest.exists()
    assert dest.read_bytes() == b"encrypted"
    assert dest.suffix == ".bak"


def test_create_backup_is_inside_backup_dir(tmp_path):
    src = tmp_path / "dev.env.age"
    src.write_bytes(b"data")
    dest = create_backup(src, base_dir=tmp_path)
    assert dest.parent == get_backup_dir(tmp_path)


def test_list_backups_empty_when_no_dir(tmp_path):
    assert list_backups("dev.env.age", base_dir=tmp_path) == []


def test_list_backups_returns_sorted(tmp_path):
    src = tmp_path / "dev.env.age"
    src.write_bytes(b"x")
    b1 = create_backup(src, base_dir=tmp_path)
    time.sleep(0.01)
    b2 = create_backup(src, base_dir=tmp_path)
    result = list_backups("dev.env.age", base_dir=tmp_path)
    assert result == sorted(result)
    assert len(result) == 2


def test_restore_backup_raises_when_missing(tmp_path):
    with pytest.raises(BackupError, match="not found"):
        restore_backup(tmp_path / "ghost.bak", tmp_path / "out.age")


def test_restore_backup_writes_dest(tmp_path):
    src = tmp_path / "dev.env.age"
    src.write_bytes(b"secret")
    bak = create_backup(src, base_dir=tmp_path)
    out = tmp_path / "restored.age"
    restore_backup(bak, out)
    assert out.read_bytes() == b"secret"


def test_prune_backups_raises_on_bad_keep(tmp_path):
    with pytest.raises(BackupError):
        prune_backups("dev.env.age", keep=0, base_dir=tmp_path)


def test_prune_backups_removes_oldest(tmp_path):
    src = tmp_path / "dev.env.age"
    src.write_bytes(b"x")
    for _ in range(4):
        create_backup(src, base_dir=tmp_path)
        time.sleep(0.01)
    deleted = prune_backups("dev.env.age", keep=2, base_dir=tmp_path)
    assert len(deleted) == 2
    remaining = list_backups("dev.env.age", base_dir=tmp_path)
    assert len(remaining) == 2
