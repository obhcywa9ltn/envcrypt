"""CLI commands for managing required env keys."""

from __future__ import annotations

import click

from envcrypt.env_required import (
    RequiredError,
    add_required_key,
    check_required,
    load_required,
    remove_required_key,
)


@click.group("required")
def required_group() -> None:
    """Manage and enforce required .env keys."""


@required_group.command("add")
@click.argument("key")
@click.option("--base-dir", default=None, help="Base directory for config.")
def cmd_required_add(key: str, base_dir: str) -> None:
    """Mark KEY as required."""
    try:
        keys = add_required_key(key, base_dir)
        click.echo(f"Added '{key}' to required keys. Total: {len(keys)}")
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@required_group.command("remove")
@click.argument("key")
@click.option("--base-dir", default=None, help="Base directory for config.")
def cmd_required_remove(key: str, base_dir: str) -> None:
    """Remove KEY from required list."""
    try:
        remove_required_key(key, base_dir)
        click.echo(f"Removed '{key}' from required keys.")
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@required_group.command("list")
@click.option("--base-dir", default=None, help="Base directory for config.")
def cmd_required_list(base_dir: str) -> None:
    """List all required keys."""
    try:
        keys = load_required(base_dir)
        if not keys:
            click.echo("No required keys defined.")
        else:
            for key in keys:
                click.echo(key)
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@required_group.command("check")
@click.argument("env_file")
@click.option("--base-dir", default=None, help="Base directory for config.")
def cmd_required_check(env_file: str, base_dir: str) -> None:
    """Check ENV_FILE has all required keys."""
    try:
        result = check_required(env_file, base_dir)
        if result.ok:
            click.echo(f"OK — all {len(result.present)} required keys present.")
        else:
            click.echo(f"MISSING keys: {', '.join(result.missing)}", err=True)
            raise SystemExit(1)
    except RequiredError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
