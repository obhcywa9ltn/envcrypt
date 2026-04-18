"""CLI commands for renaming keys in .env files."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_rename import RenameError, list_keys, rename_key


@click.group("rename")
def rename_group() -> None:
    """Rename or inspect keys in a .env file."""


@rename_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("old_key")
@click.argument("new_key")
@click.option("--dest", type=click.Path(path_type=Path), default=None, help="Output path (default: in-place)")
def cmd_rename_run(env_file: Path, old_key: str, new_key: str, dest: Path | None) -> None:
    """Rename OLD_KEY to NEW_KEY in ENV_FILE."""
    try:
        out = rename_key(env_file, old_key, new_key, dest)
        click.echo(f"Renamed '{old_key}' -> '{new_key}' in {out}")
    except RenameError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@rename_group.command("keys")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
def cmd_rename_keys(env_file: Path) -> None:
    """List all keys defined in ENV_FILE."""
    try:
        keys = list_keys(env_file)
        if keys:
            click.echo("\n".join(keys))
        else:
            click.echo("No keys found.")
    except RenameError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
