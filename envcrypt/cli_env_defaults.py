"""CLI commands for managing env key defaults."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_defaults import (
    DefaultsError,
    apply_defaults,
    load_defaults,
    remove_default,
    set_default,
)


@click.group(name="defaults")
def defaults_group() -> None:
    """Manage default values for .env keys."""


@defaults_group.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_defaults_set(key: str, value: str, base_dir: str | None) -> None:
    """Set a default value for KEY."""
    try:
        set_default(key, value, Path(base_dir) if base_dir else None)
        click.echo(f"Default set: {key}={value}")
    except DefaultsError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@defaults_group.command("remove")
@click.argument("key")
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_defaults_remove(key: str, base_dir: str | None) -> None:
    """Remove the default for KEY."""
    try:
        remove_default(key, Path(base_dir) if base_dir else None)
        click.echo(f"Default removed: {key}")
    except DefaultsError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@defaults_group.command("list")
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_defaults_list(base_dir: str | None) -> None:
    """List all configured defaults."""
    try:
        defaults = load_defaults(Path(base_dir) if base_dir else None)
        if not defaults:
            click.echo("No defaults configured.")
        else:
            for key, value in sorted(defaults.items()):
                click.echo(f"{key}={value}")
    except DefaultsError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@defaults_group.command("apply")
@click.argument("env_file", type=click.Path())
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_defaults_apply(env_file: str, base_dir: str | None) -> None:
    """Apply defaults to ENV_FILE, filling in any missing keys."""
    try:
        applied = apply_defaults(Path(env_file), Path(base_dir) if base_dir else None)
        if not applied:
            click.echo("No defaults applied (all keys already present).")
        else:
            for key, value in applied.items():
                click.echo(f"Applied: {key}={value}")
    except DefaultsError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
