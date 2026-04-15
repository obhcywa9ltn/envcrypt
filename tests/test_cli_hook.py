"""Tests for envcrypt.cli_hook"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_hook import hook_group
from envcrypt.hook import HookError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# cmd_hook_install
# ---------------------------------------------------------------------------

def test_install_prints_success(runner: CliRunner, tmp_path: Path) -> None:
    hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
    with patch("envcrypt.cli_hook.install_hook", return_value=hook_path) as mock:
        result = runner.invoke(hook_group, ["install", "--base-dir", str(tmp_path)])
    mock.assert_called_once_with(str(tmp_path))
    assert result.exit_code == 0
    assert "installed" in result.output


def test_install_exits_nonzero_on_error(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envcrypt.cli_hook.install_hook", side_effect=HookError("no git")):
        result = runner.invoke(hook_group, ["install", "--base-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "Error" in result.output


# ---------------------------------------------------------------------------
# cmd_hook_remove
# ---------------------------------------------------------------------------

def test_remove_prints_removed_when_hook_present(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envcrypt.cli_hook.remove_hook", return_value=True):
        result = runner.invoke(hook_group, ["remove", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_prints_not_installed_when_absent(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envcrypt.cli_hook.remove_hook", return_value=False):
        result = runner.invoke(hook_group, ["remove", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "not installed" in result.output


def test_remove_exits_nonzero_on_error(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envcrypt.cli_hook.remove_hook", side_effect=HookError("oops")):
        result = runner.invoke(hook_group, ["remove", "--base-dir", str(tmp_path)])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# cmd_hook_status
# ---------------------------------------------------------------------------

def test_status_prints_installed(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envcrypt.cli_hook.is_hook_installed", return_value=True):
        result = runner.invoke(hook_group, ["status", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "installed" in result.output
    assert "NOT" not in result.output


def test_status_prints_not_installed(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envcrypt.cli_hook.is_hook_installed", return_value=False):
        result = runner.invoke(hook_group, ["status", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "NOT" in result.output
