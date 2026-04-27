"""CLI commands for normalising .env key casing."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_uppercase import UppercaseError, list_non_uppercase_keys, uppercase_env_file


@click.group("uppercase")
def uppercase_group() -> None:
    """Normalise .env keys to UPPER_CASE."""


@uppercase_group.command("run")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Write output to DEST instead of modifying SRC in-place.",
)
def cmd_uppercase_run(src: Path, dest: Path | None) -> None:
    """Uppercase all keys in SRC."""
    try:
        target, changed = uppercase_env_file(src, dest)
    except UppercaseError as exc:
        raise click.ClickException(str(exc)) from exc
    if changed:
        click.echo(f"Updated {changed} key(s) in {target}")
    else:
        click.echo(f"All keys already uppercase in {target}")


@uppercase_group.command("check")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
def cmd_uppercase_check(src: Path) -> None:
    """List keys in SRC that are not fully uppercase."""
    try:
        issues = list_non_uppercase_keys(src)
    except UppercaseError as exc:
        raise click.ClickException(str(exc)) from exc
    if not issues:
        click.echo("All keys are uppercase.")
    else:
        click.echo(f"{len(issues)} key(s) need uppercasing:")
        for key in issues:
            click.echo(f"  {key}")
        raise SystemExit(1)
