"""CLI commands for backup and restore of encrypted vault files."""

import click
from envcrypt.backup import BackupError, create_backup, list_backups, restore_backup


@click.group("backup")
def backup_group():
    """Manage backups of encrypted vault files."""


@backup_group.command("create")
@click.argument("encrypted_file")
@click.option("--base-dir", default=None, help="Directory to store backups (default: .envcrypt-backups)")
def cmd_backup_create(encrypted_file: str, base_dir: str | None):
    """Create a backup of an encrypted vault file."""
    try:
        backup_path = create_backup(encrypted_file, base_dir=base_dir)
        click.echo(f"Backup created: {backup_path}")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_group.command("list")
@click.argument("encrypted_file")
@click.option("--base-dir", default=None, help="Backup directory to search")
def cmd_backup_list(encrypted_file: str, base_dir: str | None):
    """List available backups for an encrypted vault file."""
    try:
        backups = list_backups(encrypted_file, base_dir=base_dir)
        if not backups:
            click.echo("No backups found.")
        else:
            for b in backups:
                click.echo(str(b))
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_group.command("restore")
@click.argument("backup_file")
@click.argument("dest")
def cmd_backup_restore(backup_file: str, dest: str):
    """Restore a backup to the given destination path."""
    try:
        restore_backup(backup_file, dest)
        click.echo(f"Restored {backup_file} -> {dest}")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
