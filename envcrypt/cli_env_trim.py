"""CLI commands for trimming .env file values."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_trim import TrimError, trim_env_file, list_untrimmed_keys


@click.group("trim")
def trim_group() -> None:
    """Trim whitespace from .env values."""


@trim_group.command("run")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("-d", "--dest", type=click.Path(path_type=Path), default=None,
              help="Output file (default: in-place).")
@click.option("-k", "--key", "keys", multiple=True,
              help="Limit trimming to these keys (repeatable).")
def cmd_trim_run(src: Path, dest: Path | None, keys: tuple[str, ...]) -> None:
    """Trim whitespace from values in SRC."""
    try:
        changed = trim_env_file(src, dest, keys=list(keys) if keys else None)
    except TrimError as exc:
        raise click.ClickException(str(exc)) from exc

    if changed:
        for k, v in changed.items():
            click.echo(f"trimmed {k}={v!r}")
    else:
        click.echo("No values needed trimming.")


@trim_group.command("check")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
def cmd_trim_check(src: Path) -> None:
    """List keys with untrimmed values in SRC."""
    try:
        keys = list_untrimmed_keys(src)
    except TrimError as exc:
        raise click.ClickException(str(exc)) from exc

    if keys:
        for k in keys:
            click.echo(k)
    else:
        click.echo("All values are already trimmed.")
