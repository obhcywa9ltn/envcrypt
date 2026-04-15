"""Tests for CLI export sub-commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_export import export_group
from envcrypt.export import ExportError


@pytest.fixture()
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# cmd_export_push
# ---------------------------------------------------------------------------


class TestCmdExportPush:
    def test_prints_success_message(self, runner, tmp_path):
        out_file = tmp_path / "out" / "staging.age"
        with patch("envcrypt.cli_export.export_env", return_value=out_file) as mock_exp:
            result = runner.invoke(export_group, ["push", "staging", str(tmp_path / "out")])
        assert result.exit_code == 0
        assert "staging" in result.output
        mock_exp.assert_called_once()

    def test_exits_nonzero_on_error(self, runner, tmp_path):
        with patch("envcrypt.cli_export.export_env", side_effect=ExportError("boom")):
            result = runner.invoke(export_group, ["push", "staging", str(tmp_path / "out")])
        assert result.exit_code != 0
        assert "boom" in result.output


# ---------------------------------------------------------------------------
# cmd_export_pull
# ---------------------------------------------------------------------------


class TestCmdExportPull:
    def test_prints_success_message(self, runner, tmp_path):
        src = tmp_path / "staging.age"
        src.write_bytes(b"data")
        dest = tmp_path / ".envcrypt" / "vault" / "staging.age"
        with patch("envcrypt.cli_export.import_env", return_value=dest) as mock_imp:
            result = runner.invoke(
                export_group, ["pull", str(src), "staging"]
            )
        assert result.exit_code == 0
        assert "staging" in result.output
        mock_imp.assert_called_once()

    def test_exits_nonzero_on_error(self, runner, tmp_path):
        src = tmp_path / "staging.age"
        src.write_bytes(b"data")
        with patch("envcrypt.cli_export.import_env", side_effect=ExportError("oops")):
            result = runner.invoke(export_group, ["pull", str(src), "staging"])
        assert result.exit_code != 0
        assert "oops" in result.output

    def test_passes_overwrite_flag(self, runner, tmp_path):
        src = tmp_path / "staging.age"
        src.write_bytes(b"data")
        dest = tmp_path / "vault" / "staging.age"
        with patch("envcrypt.cli_export.import_env", return_value=dest) as mock_imp:
            runner.invoke(export_group, ["pull", str(src), "staging", "--overwrite"])
        _, kwargs = mock_imp.call_args
        assert kwargs.get("overwrite") is True


# ---------------------------------------------------------------------------
# cmd_export_ls
# ---------------------------------------------------------------------------


class TestCmdExportLs:
    def test_prints_entries(self, runner, tmp_path):
        entries = {"dev": Path("vault/dev.age"), "prod": Path("vault/prod.age")}
        with patch("envcrypt.cli_export.list_exports", return_value=entries):
            result = runner.invoke(export_group, ["ls"])
        assert result.exit_code == 0
        assert "dev" in result.output
        assert "prod" in result.output

    def test_prints_empty_message_when_no_entries(self, runner):
        with patch("envcrypt.cli_export.list_exports", return_value={}):
            result = runner.invoke(export_group, ["ls"])
        assert result.exit_code == 0
        assert "No encrypted files" in result.output
