"""Tests for envcrypt.cli_env_interpolate."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_env_interpolate import interpolate_group
from envcrypt.env_interpolate import InterpolateError


@pytest.fixture()
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# cmd_interpolate_run
# ---------------------------------------------------------------------------

class TestCmdInterpolateRun:
    def test_prints_success_message(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("A=1\n")
        dest = tmp_path / "out.env"
        result = runner.invoke(interpolate_group, ["run", str(src), "--dest", str(dest)])
        assert result.exit_code == 0
        assert "Interpolated" in result.output

    def test_exits_nonzero_on_error(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("A=1\n")
        with patch(
            "envcrypt.cli_env_interpolate.interpolate_env_file",
            side_effect=InterpolateError("boom"),
        ):
            result = runner.invoke(interpolate_group, ["run", str(src)])
        assert result.exit_code != 0
        assert "boom" in result.output

    def test_extra_set_flag_parsed(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("MSG=${GREETING}_world\n")
        dest = tmp_path / "out.env"
        result = runner.invoke(
            interpolate_group,
            ["run", str(src), "--dest", str(dest), "--set", "GREETING=hello"],
        )
        assert result.exit_code == 0
        assert "hello_world" in dest.read_text()

    def test_invalid_set_flag_exits_nonzero(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("A=1\n")
        result = runner.invoke(interpolate_group, ["run", str(src), "--set", "BADVALUE"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cmd_interpolate_refs
# ---------------------------------------------------------------------------

class TestCmdInterpolateRefs:
    def test_prints_refs(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("A=1\nB=${A}\n")
        result = runner.invoke(interpolate_group, ["refs", str(src)])
        assert result.exit_code == 0
        assert "B" in result.output
        assert "A" in result.output

    def test_prints_no_refs_message(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("A=plain\n")
        result = runner.invoke(interpolate_group, ["refs", str(src)])
        assert result.exit_code == 0
        assert "No variable references" in result.output

    def test_exits_nonzero_on_error(self, runner, tmp_path):
        src = tmp_path / ".env"
        src.write_text("A=1\n")
        with patch(
            "envcrypt.cli_env_interpolate.list_references",
            side_effect=InterpolateError("fail"),
        ):
            result = runner.invoke(interpolate_group, ["refs", str(src)])
        assert result.exit_code != 0
