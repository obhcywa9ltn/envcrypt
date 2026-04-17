"""CLI commands for rotation reminders."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.remind import RemindError, check_due, list_remind, record_rotation


@click.group("remind")
def remind_group() -> None:
    """Manage key-rotation reminders."""


@remind_group.command("record")
@click.argument("name")
@click.option("--base-dir", default=None, help="Directory for remind file.")
def cmd_remind_record(name: str, base_dir: str | None) -> None:
    """Record that NAME was just rotated."""
    bd = Path(base_dir) if base_dir else None
    try:
        ts = record_rotation(name, bd)
        click.echo(f"Recorded rotation for '{name}' at {ts}.")
    except RemindError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@remind_group.command("check")
@click.argument("name")
@click.option("--days", default=30, show_default=True, help="Rotation interval in days.")
@click.option("--base-dir", default=None)
def cmd_remind_check(name: str, days: int, base_dir: str | None) -> None:
    """Check whether NAME rotation is due."""
    bd = Path(base_dir) if base_dir else None
    try:
        due = check_due(name, interval_days=days, base_dir=bd)
        if due:
            click.echo(f"Rotation for '{name}' is DUE.")
        else:
            click.echo(f"Rotation for '{name}' is up to date.")
    except RemindError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@remind_group.command("list")
@click.option("--base-dir", default=None)
def cmd_remind_list(base_dir: str | None) -> None:
    """List all recorded rotations."""
    bd = Path(base_dir) if base_dir else None
    try:
        entries = list_remind(bd)
        if not entries:
            click.echo("No rotation records found.")
            return
        for name, meta in entries.items():
            click.echo(f"{name}: last rotated {meta.get('last_rotated', 'unknown')}")
    except RemindError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
