"""Integration tests for the interpolate CLI (run -> refs roundtrip)."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.cli_env_interpolate import interpolate_group


@pytest.fixture()
def runner():
    return CliRunner()


def test_run_then_refs_shows_no_refs_in_resolved(runner, tmp_path):
    """After interpolation the output file should have no variable references."""
    src = tmp_path / ".env"
    dest = tmp_path / "resolved.env"
    src.write_text("BASE=hello\nFULL=${BASE}_world\n")

    run_result = runner.invoke(interpolate_group, ["run", str(src), "--dest", str(dest)])
    assert run_result.exit_code == 0

    refs_result = runner.invoke(interpolate_group, ["refs", str(dest)])
    assert refs_result.exit_code == 0
    assert "No variable references" in refs_result.output


def test_run_resolves_chain(runner, tmp_path):
    """Chained references A -> B -> C should fully resolve."""
    src = tmp_path / ".env"
    dest = tmp_path / "out.env"
    src.write_text("A=foo\nB=${A}_bar\nC=${B}_baz\n")

    result = runner.invoke(interpolate_group, ["run", str(src), "--dest", str(dest)])
    assert result.exit_code == 0
    content = dest.read_text()
    assert "C=foo_bar_baz" in content


def test_run_with_extra_context(runner, tmp_path):
    src = tmp_path / ".env"
    dest = tmp_path / "out.env"
    src.write_text("WELCOME=${SALUTATION}_there\n")

    result = runner.invoke(
        interpolate_group,
        ["run", str(src), "--dest", str(dest), "--set", "SALUTATION=hey"],
    )
    assert result.exit_code == 0
    assert "hey_there" in dest.read_text()


def test_run_fails_for_undefined_variable(runner, tmp_path):
    src = tmp_path / ".env"
    src.write_text("X=${UNDEFINED}\n")
    result = runner.invoke(interpolate_group, ["run", str(src)])
    assert result.exit_code != 0
    assert "UNDEFINED" in result.output
