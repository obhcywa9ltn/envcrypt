"""CLI commands for vault snapshots."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.snapshot import SnapshotError, create_snapshot, delete_snapshot, list_snapshots, restore_snapshot
from envcrypt.vault import get_vault_dir


@click.group(name="snapshot")
def snapshot_group() -> None:
    """Manage vault snapshots."""


@snapshot_group.command("create")
@click.argument("name")
@click.option("--base-dir", default=None, help="Base directory (default: cwd)")
def cmd_snapshot_create(name: str, base_dir: str | None) -> None:
    """Create a snapshot of the current vault."""
    base = Path(base_dir) if base_dir else None
    try:
        vault_dir = get_vault_dir(base)
        dest = create_snapshot(name, vault_dir, base_dir=base)
        click.echo(f"Snapshot '{name}' created at {dest}")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_group.command("list")
@click.option("--base-dir", default=None)
def cmd_snapshot_list(base_dir: str | None) -> None:
    """List available snapshots."""
    base = Path(base_dir) if base_dir else None
    snaps = list_snapshots(base_dir=base)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        click.echo(f"{s.name}  {s.created_at}  ({len(s.files)} files)")


@snapshot_group.command("restore")
@click.argument("name")
@click.option("--base-dir", default=None)
def cmd_snapshot_restore(name: str, base_dir: str | None) -> None:
    """Restore vault from a snapshot."""
    base = Path(base_dir) if base_dir else None
    try:
        vault_dir = get_vault_dir(base)
        files = restore_snapshot(name, vault_dir, base_dir=base)
        click.echo(f"Restored {len(files)} file(s) from snapshot '{name}'")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_group.command("delete")
@click.argument("name")
@click.option("--base-dir", default=None)
def cmd_snapshot_delete(name: str, base_dir: str | None) -> None:
    """Delete a snapshot."""
    base = Path(base_dir) if base_dir else None
    try:
        delete_snapshot(name, base_dir=base)
        click.echo(f"Snapshot '{name}' deleted.")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
