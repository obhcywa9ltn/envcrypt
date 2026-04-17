"""CLI commands for namespace management."""
import click
from pathlib import Path
from envcrypt.namespace import NamespaceError, add_to_namespace, remove_from_namespace, list_namespaces


@click.group("namespace")
def namespace_group() -> None:
    """Manage env file namespaces."""


@namespace_group.command("add")
@click.argument("namespace")
@click.argument("env_file")
@click.option("--base-dir", default=None, help="Base directory for .envcrypt data.")
def cmd_namespace_add(namespace: str, env_file: str, base_dir: str | None) -> None:
    """Add ENV_FILE to NAMESPACE."""
    try:
        add_to_namespace(namespace, env_file, Path(base_dir) if base_dir else None)
        click.echo(f"Added {env_file!r} to namespace {namespace!r}.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("remove")
@click.argument("namespace")
@click.argument("env_file")
@click.option("--base-dir", default=None)
def cmd_namespace_remove(namespace: str, env_file: str, base_dir: str | None) -> None:
    """Remove ENV_FILE from NAMESPACE."""
    try:
        remove_from_namespace(namespace, env_file, Path(base_dir) if base_dir else None)
        click.echo(f"Removed {env_file!r} from namespace {namespace!r}.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("list")
@click.option("--base-dir", default=None)
def cmd_namespace_list(base_dir: str | None) -> None:
    """List all namespaces and their files."""
    try:
        namespaces = list_namespaces(Path(base_dir) if base_dir else None)
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not namespaces:
        click.echo("No namespaces defined.")
        return
    for ns, files in namespaces.items():
        click.echo(f"{ns}: {', '.join(files)}")
