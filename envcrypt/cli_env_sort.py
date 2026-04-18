"""CLI commands for sorting .env files."""
import click
from pathlib import Path

from envcrypt.env_sort import SortError, sort_env_file, sorted_keys


@click.group("sort")
def sort_group() -> None:
    """Sort .env file keys."""


@sort_group.command("run")
@click.argument("env_file", default=".env")
@click.option("--dest", default=None, help="Output path (defaults to in-place).")
@click.option("--reverse", is_flag=True, default=False, help="Sort descending.")
@click.option("--no-group-comments", is_flag=True, default=False)
def cmd_sort_run(env_file: str, dest: str, reverse: bool, no_group_comments: bool) -> None:
    """Sort KEY=VALUE lines in ENV_FILE alphabetically."""
    try:
        out = sort_env_file(
            Path(env_file),
            dest=Path(dest) if dest else None,
            reverse=reverse,
            group_comments=not no_group_comments,
        )
        click.echo(f"Sorted: {out}")
    except SortError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@sort_group.command("keys")
@click.argument("env_file", default=".env")
def cmd_sort_keys(env_file: str) -> None:
    """List sorted keys from ENV_FILE."""
    try:
        keys = sorted_keys(Path(env_file))
        if not keys:
            click.echo("No keys found.")
        else:
            for k in keys:
                click.echo(k)
    except SortError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
