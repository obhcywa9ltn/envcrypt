"""CLI commands for filtering .env file keys."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_filter import FilterError, exclude_keys, filter_by_keys, filter_by_pattern


@click.group("filter")
def filter_group() -> None:
    """Filter keys from a .env file."""


@filter_group.command("pick")
@click.argument("env_file", type=click.Path())
@click.argument("keys", nargs=-1, required=True)
def cmd_filter_pick(env_file: str, keys: tuple[str, ...]) -> None:
    """Print only the specified KEYS from ENV_FILE."""
    try:
        result = filter_by_keys(Path(env_file), list(keys))
    except FilterError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    for k, v in result.items():
        click.echo(f"{k}={v}")


@filter_group.command("match")
@click.argument("env_file", type=click.Path())
@click.argument("pattern")
def cmd_filter_match(env_file: str, pattern: str) -> None:
    """Print keys from ENV_FILE matching glob PATTERN."""
    try:
        result = filter_by_pattern(Path(env_file), pattern)
    except FilterError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not result:
        click.echo("No keys matched.")
        return
    for k, v in result.items():
        click.echo(f"{k}={v}")


@filter_group.command("exclude")
@click.argument("env_file", type=click.Path())
@click.argument("keys", nargs=-1, required=True)
def cmd_filter_exclude(env_file: str, keys: tuple[str, ...]) -> None:
    """Print all keys from ENV_FILE except the specified KEYS."""
    try:
        result = exclude_keys(Path(env_file), list(keys))
    except FilterError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    for k, v in result.items():
        click.echo(f"{k}={v}")
