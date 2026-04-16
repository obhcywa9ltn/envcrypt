"""Tests for envcrypt.snapshot."""
from pathlib import Path
import pytest
from envcrypt.snapshot import (
    SnapshotError,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
    get_snapshot_dir,
)


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "dev.env.age").write_text("encrypted-dev")
    (vault / "prod.env.age").write_text("encrypted-prod")
    return vault


def test_get_snapshot_dir_defaults_to_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert get_snapshot_dir() == tmp_path / ".envcrypt" / "snapshots"


def test_get_snapshot_dir_uses_base_dir(tmp_path):
    assert get_snapshot_dir(tmp_path) == tmp_path / ".envcrypt" / "snapshots"


def test_create_snapshot_raises_when_vault_missing(tmp_path):
    with pytest.raises(SnapshotError, match="Vault directory not found"):
        create_snapshot("snap1", tmp_path / "nonexistent", base_dir=tmp_path)


def test_create_snapshot_copies_age_files(tmp_path):
    vault = _make_vault(tmp_path)
    dest = create_snapshot("snap1", vault, base_dir=tmp_path)
    assert (dest / "dev.env.age").exists()
    assert (dest / "prod.env.age").exists()


def test_create_snapshot_writes_meta(tmp_path):
    vault = _make_vault(tmp_path)
    create_snapshot("snap1", vault, base_dir=tmp_path)
    snaps = list_snapshots(base_dir=tmp_path)
    assert len(snaps) == 1
    assert snaps[0].name == "snap1"
    assert len(snaps[0].files) == 2


def test_create_snapshot_raises_on_duplicate(tmp_path):
    vault = _make_vault(tmp_path)
    create_snapshot("snap1", vault, base_dir=tmp_path)
    with pytest.raises(SnapshotError, match="already exists"):
        create_snapshot("snap1", vault, base_dir=tmp_path)


def test_list_snapshots_empty_when_no_dir(tmp_path):
    assert list_snapshots(base_dir=tmp_path) == []


def test_restore_snapshot_raises_when_missing(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot("nope", tmp_path / "vault", base_dir=tmp_path)


def test_restore_snapshot_copies_files_back(tmp_path):
    vault = _make_vault(tmp_path)
    create_snapshot("snap1", vault, base_dir=tmp_path)
    restore_dir = tmp_path / "vault2"
    restored = restore_snapshot("snap1", restore_dir, base_dir=tmp_path)
    assert len(restored) == 2
    assert (restore_dir / "dev.env.age").read_text() == "encrypted-dev"


def test_delete_snapshot_removes_entry(tmp_path):
    vault = _make_vault(tmp_path)
    create_snapshot("snap1", vault, base_dir=tmp_path)
    delete_snapshot("snap1", base_dir=tmp_path)
    assert list_snapshots(base_dir=tmp_path) == []


def test_delete_snapshot_raises_when_missing(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot("ghost", base_dir=tmp_path)
