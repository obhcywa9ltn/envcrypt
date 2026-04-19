"""CLI commands for env key grouping."""
import click
from envcrypt.env_group import GroupError, add_to_group, remove_from_group, list_groups


@click.group("group")
def group_cmd():
    """Manage named groups of env keys."""


@group_cmd.command("add")
@click.argument("group")
@click.argument("key")
@click.option("--base-dir", default=None, help="Base directory for groups file.")
def cmd_group_add(group: str, key: str, base_dir: str | None):
    """Add KEY to GROUP."""
    try:
        add_to_group(group, key, base_dir)
        click.echo(f"Added '{key}' to group '{group}'.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_cmd.command("remove")
@click.argument("group")
@click.argument("key")
@click.option("--base-dir", default=None)
def cmd_group_remove(group: str, key: str, base_dir: str | None):
    """Remove KEY from GROUP."""
    try:
        remove_from_group(group, key, base_dir)
        click.echo(f"Removed '{key}' from group '{group}'.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_cmd.command("list")
@click.option("--base-dir", default=None)
def cmd_group_list(base_dir: str | None):
    """List all groups and their keys."""
    try:
        groups = list_groups(base_dir)
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not groups:
        click.echo("No groups defined.")
        return
    for name, keys in groups.items():
        click.echo(f"{name}: {', '.join(keys)}")
