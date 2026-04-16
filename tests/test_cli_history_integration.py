"""Integration tests for history CLI roundtrip."""
import pytest
from click.testing import CliRunner

from envcrypt.cli_history import history_group


@pytest.fixture()
def runner():
    return CliRunner()


def test_record_then_log_roundtrip(runner, tmp_path):
    runner.invoke(
        history_group,
        ["record", "lock", ".env", "--actor", "dave", "--base-dir", str(tmp_path)],
    )
    runner.invoke(
        history_group,
        ["record", "unlock", ".env.staging", "--actor", "eve", "--base-dir", str(tmp_path)],
    )
    result = runner.invoke(history_group, ["log", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "lock" in result.output
    assert "unlock" in result.output
    assert "dave" in result.output
    assert "eve" in result.output


def test_record_clear_log_shows_empty(runner, tmp_path):
    runner.invoke(
        history_group,
        ["record", "lock", ".env", "--base-dir", str(tmp_path)],
    )
    runner.invoke(
        history_group,
        ["clear", "--base-dir", str(tmp_path)],
        input="y\n",
    )
    result = runner.invoke(history_group, ["log", "--base-dir", str(tmp_path)])
    assert "No history" in result.output


def test_log_limit_respected(runner, tmp_path):
    for i in range(5):
        runner.invoke(
            history_group,
            ["record", f"action{i}", ".env", "--base-dir", str(tmp_path)],
        )
    result = runner.invoke(history_group, ["log", "--limit", "2", "--base-dir", str(tmp_path)])
    lines = [l for l in result.output.splitlines() if "action" in l]
    assert len(lines) == 2
