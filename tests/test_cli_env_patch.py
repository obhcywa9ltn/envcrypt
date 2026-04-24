"""Tests for envcrypt.cli_env_patch CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_env_patch import patch_group
from envcrypt.env_patch import PatchError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=val\nOTHER=stuff\n")
    return p


def test_run_prints_success(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(patch_group, ["run", str(env_file), "--set", "KEY=new"])
    assert result.exit_code == 0
    assert "Patched" in result.output
    assert "1 set" in result.output


def test_run_exits_nonzero_on_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(patch_group, ["run", str(tmp_path / "missing.env"), "--set", "A=1"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_run_bad_set_flag(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(patch_group, ["run", str(env_file), "--set", "NOEQUALS"])
    assert result.exit_code != 0


def test_run_remove_flag(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(patch_group, ["run", str(env_file), "--remove", "OTHER"])
    assert result.exit_code == 0
    assert "1 removed" in result.output


def test_run_writes_dest(runner: CliRunner, env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.env"
    result = runner.invoke(
        patch_group, ["run", str(env_file), "--set", "KEY=x", "--dest", str(dest)]
    )
    assert result.exit_code == 0
    assert dest.exists()


def test_keys_lists_keys(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(patch_group, ["keys", str(env_file)])
    assert result.exit_code == 0
    assert "KEY" in result.output
    assert "OTHER" in result.output


def test_keys_exits_nonzero_on_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(patch_group, ["keys", str(tmp_path / "nope.env")])
    assert result.exit_code != 0
    assert "Error" in result.output
