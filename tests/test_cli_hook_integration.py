"""Integration tests for the hook CLI commands against a real fake git repo."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.cli_hook import hook_group
from envcrypt.hook import HOOK_MARKER, get_hook_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


def test_install_status_remove_roundtrip(runner: CliRunner, git_repo: Path) -> None:
    base = str(git_repo)

    # Initially not installed
    result = runner.invoke(hook_group, ["status", "--base-dir", base])
    assert "NOT" in result.output

    # Install
    result = runner.invoke(hook_group, ["install", "--base-dir", base])
    assert result.exit_code == 0
    assert "installed" in result.output

    # Status shows installed
    result = runner.invoke(hook_group, ["status", "--base-dir", base])
    assert "NOT" not in result.output

    # Remove
    result = runner.invoke(hook_group, ["remove", "--base-dir", base])
    assert result.exit_code == 0
    assert "removed" in result.output

    # Status shows not installed
    result = runner.invoke(hook_group, ["status", "--base-dir", base])
    assert "NOT" in result.output


def test_install_fails_without_git_dir(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(hook_group, ["install", "--base-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_install_twice_does_not_duplicate_marker(runner: CliRunner, git_repo: Path) -> None:
    base = str(git_repo)
    runner.invoke(hook_group, ["install", "--base-dir", base])
    runner.invoke(hook_group, ["install", "--base-dir", base])
    content = get_hook_path(base).read_text()
    assert content.count(HOOK_MARKER) == 1
