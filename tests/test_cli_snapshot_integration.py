"""Integration tests for snapshot CLI roundtrip."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.cli_snapshot import snapshot_group


@pytest.fixture()
def runner():
    return CliRunner()


def _make_vault(base: Path) -> Path:
    vault = base / ".envcrypt" / "vault"
    vault.mkdir(parents=True)
    (vault / "dev.env.age").write_text("enc-dev")
    return vault


def test_create_list_delete_roundtrip(runner, tmp_path):
    _make_vault(tmp_path)
    r = runner.invoke(snapshot_group, ["create", "snap1", "--base-dir", str(tmp_path)])
    assert r.exit_code == 0, r.output

    r = runner.invoke(snapshot_group, ["list", "--base-dir", str(tmp_path)])
    assert "snap1" in r.output

    r = runner.invoke(snapshot_group, ["delete", "snap1", "--base-dir", str(tmp_path)])
    assert r.exit_code == 0

    r = runner.invoke(snapshot_group, ["list", "--base-dir", str(tmp_path)])
    assert "No snapshots" in r.output


def test_restore_overwrites_vault(runner, tmp_path):
    vault = _make_vault(tmp_path)
    runner.invoke(snapshot_group, ["create", "snap1", "--base-dir", str(tmp_path)])

    # Corrupt the vault file
    (vault / "dev.env.age").write_text("corrupted")

    r = runner.invoke(snapshot_group, ["restore", "snap1", "--base-dir", str(tmp_path)])
    assert r.exit_code == 0
    assert (vault / "dev.env.age").read_text() == "enc-dev"


def test_create_duplicate_fails(runner, tmp_path):
    _make_vault(tmp_path)
    runner.invoke(snapshot_group, ["create", "snap1", "--base-dir", str(tmp_path)])
    r = runner.invoke(snapshot_group, ["create", "snap1", "--base-dir", str(tmp_path)])
    assert r.exit_code == 1
    assert "already exists" in r.output
