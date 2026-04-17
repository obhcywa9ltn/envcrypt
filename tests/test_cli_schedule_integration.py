"""Integration tests for schedule CLI (add/list/due/mark-done/remove roundtrip)."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.cli_schedule import schedule_group
from envcrypt.schedule import get_schedule_path, load_schedule, update_last_run


@pytest.fixture()
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return CliRunner()


def test_add_list_remove_roundtrip(runner):
    result = runner.invoke(schedule_group, ["add", "rotate", "--days", "14"])
    assert result.exit_code == 0

    result = runner.invoke(schedule_group, ["list"])
    assert "rotate" in result.output
    assert "14" in result.output

    result = runner.invoke(schedule_group, ["remove", "rotate"])
    assert result.exit_code == 0

    result = runner.invoke(schedule_group, ["list"])
    assert "No schedules" in result.output


def test_due_after_add(runner):
    runner.invoke(schedule_group, ["add", "sync", "--days", "7"])
    result = runner.invoke(schedule_group, ["due"])
    assert "DUE" in result.output
    assert "sync" in result.output


def test_mark_done_clears_due(runner):
    runner.invoke(schedule_group, ["add", "sync", "--days", "7"])
    runner.invoke(schedule_group, ["mark-done", "sync"])
    result = runner.invoke(schedule_group, ["due"])
    assert "No schedules due" in result.output


def test_add_duplicate_fails(runner):
    runner.invoke(schedule_group, ["add", "sync", "--days", "7"])
    result = runner.invoke(schedule_group, ["add", "sync", "--days", "14"])
    assert result.exit_code != 0
    assert "already exists" in result.output
