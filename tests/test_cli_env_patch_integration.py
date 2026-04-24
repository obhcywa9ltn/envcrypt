"""Integration tests for the env-patch CLI (run -> keys roundtrip)."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.cli_env_patch import patch_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("ALPHA=1\nBETA=2\nGAMMA=3\n")
    return p


def test_set_then_keys_shows_new_key(runner: CliRunner, env_file: Path) -> None:
    runner.invoke(patch_group, ["run", str(env_file), "--set", "DELTA=4"])
    result = runner.invoke(patch_group, ["keys", str(env_file)])
    assert "DELTA" in result.output


def test_remove_then_keys_hides_key(runner: CliRunner, env_file: Path) -> None:
    runner.invoke(patch_group, ["run", str(env_file), "--remove", "BETA"])
    result = runner.invoke(patch_group, ["keys", str(env_file)])
    assert "BETA" not in result.output
    assert "ALPHA" in result.output


def test_multiple_set_and_remove(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(
        patch_group,
        [
            "run", str(env_file),
            "--set", "ALPHA=updated",
            "--set", "NEW=hello",
            "--remove", "GAMMA",
        ],
    )
    assert result.exit_code == 0
    text = env_file.read_text()
    assert "ALPHA=updated" in text
    assert "NEW=hello" in text
    assert "GAMMA" not in text


def test_idempotent_set(runner: CliRunner, env_file: Path) -> None:
    runner.invoke(patch_group, ["run", str(env_file), "--set", "ALPHA=same"])
    runner.invoke(patch_group, ["run", str(env_file), "--set", "ALPHA=same"])
    text = env_file.read_text()
    assert text.count("ALPHA=") == 1
