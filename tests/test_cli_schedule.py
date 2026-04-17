"""Tests for envcrypt.cli_schedule."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_schedule import schedule_group
from envcrypt.schedule import ScheduleEntry, ScheduleError


@pytest.fixture()
def runner():
    return CliRunner()


def test_add_prints_success(runner):
    with patch("envcrypt.cli_schedule.add_schedule") as mock:
        mock.return_value = ScheduleEntry(name="rotate", interval_days=30)
        result = runner.invoke(schedule_group, ["add", "rotate", "--days", "30"])
    assert result.exit_code == 0
    assert "rotate" in result.output
    assert "30" in result.output


def test_add_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_schedule.add_schedule", side_effect=ScheduleError("dup")):
        result = runner.invoke(schedule_group, ["add", "rotate", "--days", "30"])
    assert result.exit_code != 0
    assert "dup" in result.output


def test_remove_prints_success(runner):
    with patch("envcrypt.cli_schedule.remove_schedule"):
        result = runner.invoke(schedule_group, ["remove", "rotate"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_schedule.remove_schedule", side_effect=ScheduleError("nf")):
        result = runner.invoke(schedule_group, ["remove", "rotate"])
    assert result.exit_code != 0


def test_list_shows_entries(runner):
    entries = {"sync": ScheduleEntry(name="sync", interval_days=7, last_run="2024-01-01")}
    with patch("envcrypt.cli_schedule.load_schedule", return_value=entries):
        result = runner.invoke(schedule_group, ["list"])
    assert result.exit_code == 0
    assert "sync" in result.output
    assert "7" in result.output


def test_list_prints_empty_message(runner):
    with patch("envcrypt.cli_schedule.load_schedule", return_value={}):
        result = runner.invoke(schedule_group, ["list"])
    assert "No schedules" in result.output


def test_due_shows_due_entries(runner):
    due = [ScheduleEntry(name="rotate", interval_days=30)]
    with patch("envcrypt.cli_schedule.due_schedules", return_value=due):
        result = runner.invoke(schedule_group, ["due"])
    assert result.exit_code == 0
    assert "DUE" in result.output
    assert "rotate" in result.output


def test_due_prints_none_message(runner):
    with patch("envcrypt.cli_schedule.due_schedules", return_value=[]):
        result = runner.invoke(schedule_group, ["due"])
    assert "No schedules due" in result.output


def test_mark_done_prints_success(runner):
    with patch("envcrypt.cli_schedule.update_last_run"):
        result = runner.invoke(schedule_group, ["mark-done", "rotate"])
    assert result.exit_code == 0
    assert "done" in result.output


def test_mark_done_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_schedule.update_last_run", side_effect=ScheduleError("nf")):
        result = runner.invoke(schedule_group, ["mark-done", "rotate"])
    assert result.exit_code != 0
