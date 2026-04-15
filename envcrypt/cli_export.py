"""CLI sub-commands for export / import of encrypted env files."""

from __future__ import annotations

from pathlib import Path

import click

from envcrypt.export import ExportError, export_env, import_env, list_exports


@click.group("export")
def export_group() -> None:
    """Export and import encrypted .env files."""


@export_group.command("push")
@click.argument("name")
@click.argument("dest", type=click.Path())
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_export_push(name: str, dest: str, base_dir: str | None) -> None:
    """Export encrypted file NAME to DEST directory."""
    base = Path(base_dir) if base_dir else None
    try:
        out = export_env(name, Path(dest), base_dir=base)
        click.echo(f"Exported '{name}' to {out}")
    except ExportError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@export_group.command("pull")
@click.argument("src", type=click.Path(exists=True))
@click.argument("name")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing vault entry.")
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_export_pull(src: str, name: str, overwrite: bool, base_dir: str | None) -> None:
    """Import encrypted file SRC into vault as NAME."""
    base = Path(base_dir) if base_dir else None
    try:
        dest = import_env(Path(src), name, base_dir=base, overwrite=overwrite)
        click.echo(f"Imported '{name}' from {src} -> {dest}")
    except ExportError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@export_group.command("ls")
@click.option("--base-dir", default=None, type=click.Path(), help="Project base directory.")
def cmd_export_ls(base_dir: str | None) -> None:
    """List all encrypted vault entries available for export."""
    base = Path(base_dir) if base_dir else None
    entries = list_exports(base_dir=base)
    if not entries:
        click.echo("No encrypted files found in vault.")
        return
    for name, path in entries.items():
        click.echo(f"  {name}  ->  {path}")
