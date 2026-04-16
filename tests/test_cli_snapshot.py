"""Tests for envcrypt.cli_snapshot."""
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_snapshot import snapshot_group
from envcrypt.snapshot import SnapshotError, SnapshotMeta


@pytest.fixture()
def runner():
    return CliRunner()


def test_create_prints_success(runner, tmp_path):
    with patch("envcrypt.cli_snapshot.get_vault_dir") as gvd, \
         patch("envcrypt.cli_snapshot.create_snapshot") as cs:
        gvd.return_value = tmp_path / "vault"
        cs.return_value = tmp_path / ".envcrypt" / "snapshots" / "snap1"
        result = runner.invoke(snapshot_group, ["create", "snap1", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "snap1" in result.output


def test_create_exits_nonzero_on_error(runner, tmp_path):
    with patch("envcrypt.cli_snapshot.get_vault_dir") as gvd, \
         patch("envcrypt.cli_snapshot.create_snapshot", side_effect=SnapshotError("boom")):
        gvd.return_value = tmp_path / "vault"
        result = runner.invoke(snapshot_group, ["create", "snap1", "--base-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "boom" in result.output


def test_list_shows_entries(runner, tmp_path):
    snaps = [SnapshotMeta(name="s1", created_at="2024-01-01T00:00:00+00:00", files=["a.age"])]
    with patch("envcrypt.cli_snapshot.list_snapshots", return_value=snaps):
        result = runner.invoke(snapshot_group, ["list", "--base-dir", str(tmp_path)])
    assert "s1" in result.output
    assert result.exit_code == 0


def test_list_prints_empty_message(runner, tmp_path):
    with patch("envcrypt.cli_snapshot.list_snapshots", return_value=[]):
        result = runner.invoke(snapshot_group, ["list", "--base-dir", str(tmp_path)])
    assert "No snapshots" in result.output


def test_restore_prints_success(runner, tmp_path):
    with patch("envcrypt.cli_snapshot.get_vault_dir") as gvd, \
         patch("envcrypt.cli_snapshot.restore_snapshot", return_value=["a.age", "b.age"]):
        gvd.return_value = tmp_path / "vault"
        result = runner.invoke(snapshot_group, ["restore", "snap1", "--base-dir", str(tmp_path)])
    assert "2" in result.output
    assert result.exit_code == 0


def test_delete_prints_success(runner, tmp_path):
    with patch("envcrypt.cli_snapshot.delete_snapshot"):
        result = runner.invoke(snapshot_group, ["delete", "snap1", "--base-dir", str(tmp_path)])
    assert "deleted" in result.output
    assert result.exit_code == 0


def test_delete_exits_nonzero_on_error(runner, tmp_path):
    with patch("envcrypt.cli_snapshot.delete_snapshot", side_effect=SnapshotError("nope")):
        result = runner.invoke(snapshot_group, ["delete", "ghost", "--base-dir", str(tmp_path)])
    assert result.exit_code == 1
