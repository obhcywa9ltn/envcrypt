"""CLI commands for managing the envcrypt git pre-commit hook."""

from __future__ import annotations

import click

from envcrypt.hook import HookError, install_hook, is_hook_installed, remove_hook


@click.group(name="hook")
def hook_group() -> None:
    """Manage the envcrypt git pre-commit hook."""


@hook_group.command(name="install")
@click.option(
    "--base-dir",
    default=None,
    help="Repository root (defaults to current directory).",
)
def cmd_hook_install(base_dir: str | None) -> None:
    """Install the pre-commit hook that auto-locks .env files."""
    try:
        path = install_hook(base_dir)
        click.echo(f"envcrypt hook installed: {path}")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@hook_group.command(name="remove")
@click.option(
    "--base-dir",
    default=None,
    help="Repository root (defaults to current directory).",
)
def cmd_hook_remove(base_dir: str | None) -> None:
    """Remove the envcrypt pre-commit hook."""
    try:
        removed = remove_hook(base_dir)
        if removed:
            click.echo("envcrypt hook removed.")
        else:
            click.echo("envcrypt hook was not installed.")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@hook_group.command(name="status")
@click.option(
    "--base-dir",
    default=None,
    help="Repository root (defaults to current directory).",
)
def cmd_hook_status(base_dir: str | None) -> None:
    """Check whether the envcrypt pre-commit hook is installed."""
    installed = is_hook_installed(base_dir)
    if installed:
        click.echo("envcrypt hook is installed.")
    else:
        click.echo("envcrypt hook is NOT installed.")
