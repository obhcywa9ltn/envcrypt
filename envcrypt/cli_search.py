"""CLI commands for vault search."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.search import SearchError, search_vault


@click.group(name="search")
def search_group() -> None:
    """Search keys and values across encrypted vault files."""


@search_group.command(name="run")
@click.argument("pattern")
@click.option("--values", is_flag=True, default=False, help="Also search values.")
@click.option("--key-file", "key_file", default=None, help="Path to age private key.")
def cmd_search_run(pattern: str, values: bool, key_file: str | None) -> None:
    """Search for PATTERN in vault key names (and optionally values)."""
    kf = Path(key_file) if key_file else None
    try:
        result = search_vault(pattern, key_file=kf, search_values=values)
    except SearchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not result.found:
        click.echo("No matches found.")
        return

    for match in result.matches:
        if values:
            click.echo(f"[{match.env_name}] {match.key}={match.value}")
        else:
            click.echo(f"[{match.env_name}] {match.key}")
