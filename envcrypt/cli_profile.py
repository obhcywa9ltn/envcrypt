"""CLI commands for managing environment profiles."""

from __future__ import annotations

import click

from envcrypt.profile import (
    ProfileError,
    add_profile,
    list_profiles,
    remove_profile,
    update_profile,
)


@click.group("profile")
def profile_group() -> None:
    """Manage named environment profiles."""


@profile_group.command("add")
@click.argument("name")
@click.argument("env_path")
def cmd_profile_add(name: str, env_path: str) -> None:
    """Register a new profile NAME pointing to ENV_PATH."""
    try:
        profiles = add_profile(name, env_path)
        click.echo(f"Profile '{name}' added -> {env_path}")
        click.echo(f"Total profiles: {len(profiles)}")
    except ProfileError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("update")
@click.argument("name")
@click.argument("env_path")
def cmd_profile_update(name: str, env_path: str) -> None:
    """Update an existing profile NAME to point to ENV_PATH."""
    try:
        update_profile(name, env_path)
        click.echo(f"Profile '{name}' updated -> {env_path}")
    except ProfileError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("remove")
@click.argument("name")
def cmd_profile_remove(name: str) -> None:
    """Remove a profile by NAME."""
    try:
        remove_profile(name)
        click.echo(f"Profile '{name}' removed.")
    except ProfileError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("list")
def cmd_profile_list() -> None:
    """List all registered profiles."""
    names = list_profiles()
    if not names:
        click.echo("No profiles registered.")
        return
    for name in names:
        click.echo(name)
