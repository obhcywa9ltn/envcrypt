"""CLI commands for managing envcrypt schedules."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import click

from envcrypt.schedule import (
    ScheduleError,
    add_schedule,
    remove_schedule,
    load_schedule,
    due_schedules,
    update_last_run,
)


@click.group("schedule")
def schedule_group() -> None:
    """Manage rotation/sync schedules."""


@schedule_group.command("add")
@click.argument("name")
@click.option("--days", required=True, type=int, help="Interval in days")
def cmd_schedule_add(name: str, days: int) -> None:
    """Add a new schedule entry."""
    try:
        entry = add_schedule(name, days)
        click.echo(f"Schedule '{entry.name}' added (every {entry.interval_days} days).")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_group.command("remove")
@click.argument("name")
def cmd_schedule_remove(name: str) -> None:
    """Remove a schedule entry."""
    try:
        remove_schedule(name)
        click.echo(f"Schedule '{name}' removed.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_group.command("list")
def cmd_schedule_list() -> None:
    """List all schedule entries."""
    try:
        entries = load_schedule()
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not entries:
        click.echo("No schedules defined.")
        return
    for entry in entries.values():
        last = entry.last_run or "never"
        click.echo(f"{entry.name}: every {entry.interval_days} days, last run: {last}")


@schedule_group.command("due")
def cmd_schedule_due() -> None:
    """Show schedules that are currently due."""
    try:
        due = due_schedules()
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not due:
        click.echo("No schedules due.")
        return
    for entry in due:
        click.echo(f"DUE: {entry.name} (every {entry.interval_days} days)")


@schedule_group.command("mark-done")
@click.argument("name")
def cmd_schedule_mark_done(name: str) -> None:
    """Mark a schedule as run today."""
    try:
        today = date.today().isoformat()
        update_last_run(name, today)
        click.echo(f"Schedule '{name}' marked as done on {today}.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
