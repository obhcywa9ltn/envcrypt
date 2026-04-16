"""Tests for envcrypt.cli_history."""
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_history import history_group
from envcrypt.history import HistoryError


@pytest.fixture()
def runner():
    return CliRunner()


def test_log_prints_no_history_when_empty(runner, tmp_path):
    result = runner.invoke(history_group, ["log", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_log_shows_entries(runner, tmp_path):
    from envcrypt.history import record_event
    record_event("lock", ".env", actor="bob", base_dir=tmp_path)
    result = runner.invoke(history_group, ["log", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "lock" in result.output
    assert "bob" in result.output


def test_log_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_history.load_history", side_effect=HistoryError("bad")):
        result = runner.invoke(history_group, ["log"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_clear_removes_entries(runner, tmp_path):
    from envcrypt.history import record_event, load_history
    record_event("lock", ".env", base_dir=tmp_path)
    result = runner.invoke(history_group, ["clear", "--base-dir", str(tmp_path)], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()
    assert load_history(tmp_path) == []


def test_record_adds_entry(runner, tmp_path):
    result = runner.invoke(
        history_group,
        ["record", "unlock", ".env", "--actor", "carol", "--base-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "Recorded" in result.output


def test_record_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_history.record_event", side_effect=HistoryError("oops")):
        result = runner.invoke(history_group, ["record", "lock", ".env"])
    assert result.exit_code != 0
