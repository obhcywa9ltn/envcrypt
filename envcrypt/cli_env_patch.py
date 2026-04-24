"""CLI commands for patching .env files."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import click

from envcrypt.env_patch import PatchError, patch_env_file, list_patch_keys


@click.group("patch")
def patch_group() -> None:
    """Patch keys in an .env file."""


@patch_group.command("run")
@click.argument("env_file", type=click.Path())
@click.option("-s", "--set", "sets", multiple=True, metavar="KEY=VALUE",
              help="Set or update a key (can be repeated).")
@click.option("-r", "--remove", "removals", multiple=True, metavar="KEY",
              help="Remove a key (can be repeated).")
@click.option("--dest", default=None, type=click.Path(),
              help="Write output to DEST instead of modifying in place.")
def cmd_patch_run(
    env_file: str,
    sets: Tuple[str, ...],
    removals: Tuple[str, ...],
    dest: Optional[str],
) -> None:
    """Apply SET and REMOVE operations to ENV_FILE."""
    updates = {}
    for item in sets:
        if "=" not in item:
            raise click.BadParameter(f"expected KEY=VALUE, got: {item}", param_hint="--set")
        key, _, value = item.partition("=")
        updates[key.strip()] = value.strip()

    try:
        added_updated, removed = patch_env_file(
            Path(env_file),
            updates=updates,
            removals=list(removals),
            dest=Path(dest) if dest else None,
        )
        click.echo(f"Patched {env_file}: {added_updated} set, {removed} removed.")
    except PatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@patch_group.command("keys")
@click.argument("env_file", type=click.Path())
def cmd_patch_keys(env_file: str) -> None:
    """List keys defined in ENV_FILE."""
    try:
        keys = list_patch_keys(Path(env_file))
        if keys:
            for k in keys:
                click.echo(k)
        else:
            click.echo("(no keys defined)")
    except PatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
