"""Tests for envcrypt.cli_share CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_share import share_group
from envcrypt.share import ShareError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# cmd_share_push
# ---------------------------------------------------------------------------

class TestCmdSharePush:
    def test_prints_success_message(self, runner, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val")
        out_path = tmp_path / "shares" / ".env.alice.age"
        with patch("envcrypt.cli_share.share_with", return_value={"alice": out_path}):
            result = runner.invoke(
                share_group, ["push", str(env_file), "alice", "--dest", str(tmp_path / "shares")]
            )
        assert result.exit_code == 0
        assert "alice" in result.output
        assert str(out_path) in result.output

    def test_exits_nonzero_on_error(self, runner, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val")
        with patch("envcrypt.cli_share.share_with", side_effect=ShareError("boom")):
            result = runner.invoke(
                share_group, ["push", str(env_file), "alice"]
            )
        assert result.exit_code != 0
        assert "boom" in result.output


# ---------------------------------------------------------------------------
# cmd_share_pull
# ---------------------------------------------------------------------------

class TestCmdSharePull:
    def test_prints_decrypted_path(self, runner, tmp_path):
        shared = tmp_path / "file.age"
        shared.write_bytes(b"data")
        key = tmp_path / "key.txt"
        key.write_text("AGE-SECRET-KEY-1")
        dest = tmp_path / ".env"
        with patch("envcrypt.cli_share.receive_share", return_value=dest):
            result = runner.invoke(
                share_group,
                ["pull", str(shared), str(dest), "--key", str(key)],
            )
        assert result.exit_code == 0
        assert str(dest) in result.output

    def test_exits_nonzero_on_error(self, runner, tmp_path):
        shared = tmp_path / "file.age"
        shared.write_bytes(b"data")
        key = tmp_path / "key.txt"
        key.write_text("AGE-SECRET-KEY-1")
        dest = tmp_path / ".env"
        with patch("envcrypt.cli_share.receive_share", side_effect=ShareError("bad key")):
            result = runner.invoke(
                share_group,
                ["pull", str(shared), str(dest), "--key", str(key)],
            )
        assert result.exit_code != 0
        assert "bad key" in result.output


# ---------------------------------------------------------------------------
# cmd_share_ls
# ---------------------------------------------------------------------------

class TestCmdShareLs:
    def test_prints_no_files_when_empty(self, runner, tmp_path):
        with patch("envcrypt.cli_share.list_shares", return_value=[]):
            result = runner.invoke(share_group, ["ls", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "No share files found" in result.output

    def test_lists_share_files(self, runner, tmp_path):
        files = [tmp_path / "a.age", tmp_path / "b.age"]
        with patch("envcrypt.cli_share.list_shares", return_value=files):
            result = runner.invoke(share_group, ["ls", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "a.age" in result.output
        assert "b.age" in result.output
