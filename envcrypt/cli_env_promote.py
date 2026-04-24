"""CLI commands for promoting env values between environments."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_promote import PromoteError, list_promotable_keys, promote_keys


@click.group("promote")
def promote_group() -> None:
    """Promote .env values across environments."""


@promote_group.command("run")
@click.argument("src", type=click.Path())
@click.argument("dest", type=click.Path())
@click.option("-k", "--key", "keys", multiple=True, help="Key(s) to promote (default: all).")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in dest.")
def cmd_promote_run(src: str, dest: str, keys: tuple, overwrite: bool) -> None:
    """Promote keys from SRC env file into DEST env file."""
    try:
        promoted = promote_keys(
            Path(src),
            Path(dest),
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except PromoteError as exc:
        raise click.ClickException(str(exc)) from exc

    for key in promoted:
        click.echo(f"promoted: {key}")
    click.echo(f"Done — {len(promoted)} key(s) promoted to {dest}")


@promote_group.command("diff")
@click.argument("src", type=click.Path())
@click.argument("dest", type=click.Path())
def cmd_promote_diff(src: str, dest: str) -> None:
    """Show which keys in SRC are new or already present in DEST."""
    try:
        categories = list_promotable_keys(Path(src), Path(dest))
    except PromoteError as exc:
        raise click.ClickException(str(exc)) from exc

    if categories["new"]:
        click.echo("New keys (not in dest):")
        for k in categories["new"]:
            click.echo(f"  + {k}")
    else:
        click.echo("No new keys to promote.")

    if categories["existing"]:
        click.echo("Existing keys (already in dest):")
        for k in categories["existing"]:
            click.echo(f"  ~ {k}")
