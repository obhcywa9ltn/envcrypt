"""CLI commands for managing .env key aliases."""

import click
from envcrypt.alias import AliasError, add_alias, remove_alias, load_aliases, get_aliases_path


@click.group("alias")
def alias_group():
    """Manage key aliases for .env variables."""


@alias_group.command("add")
@click.argument("key")
@click.argument("alias")
@click.option("--base-dir", default=None, help="Base directory for aliases file.")
def cmd_alias_add(key: str, alias: str, base_dir: str):
    """Add an alias for a .env key."""
    try:
        add_alias(key, alias, base_dir=base_dir)
        click.echo(f"Alias '{alias}' -> '{key}' added.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("remove")
@click.argument("alias")
@click.option("--base-dir", default=None, help="Base directory for aliases file.")
def cmd_alias_remove(alias: str, base_dir: str):
    """Remove an alias."""
    try:
        remove_alias(alias, base_dir=base_dir)
        click.echo(f"Alias '{alias}' removed.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("list")
@click.option("--base-dir", default=None, help="Base directory for aliases file.")
def cmd_alias_list(base_dir: str):
    """List all defined aliases."""
    try:
        aliases = load_aliases(base_dir=base_dir)
        if not aliases:
            click.echo("No aliases defined.")
            return
        for alias, key in sorted(aliases.items()):
            click.echo(f"  {alias} -> {key}")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
