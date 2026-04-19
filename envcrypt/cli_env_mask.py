"""CLI commands for masking env variable values."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_mask import MaskError, mask_env_file, show_masked


@click.group("mask")
def mask_group() -> None:
    """Mask env variable values for safe display."""


@mask_group.command("run")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--dest", type=click.Path(path_type=Path), default=None, help="Output file path.")
@click.option("--key", "keys", multiple=True, help="Keys to mask (default: all).")
@click.option("--visible", default=4, show_default=True, help="Trailing chars to keep visible.")
@click.option("--char", default="*", show_default=True, help="Mask character.")
def cmd_mask_run(
    src: Path,
    dest: Path | None,
    keys: tuple[str, ...],
    visible: int,
    char: str,
) -> None:
    """Write a masked copy of SRC."""
    try:
        masked = mask_env_file(src, dest=dest, keys=list(keys) or None, visible=visible, char=char)
        out = dest or src.with_suffix(".masked")
        click.echo(f"Masked {len(masked)} key(s) -> {out}")
    except MaskError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@mask_group.command("show")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--key", "keys", multiple=True, help="Keys to display (default: all).")
@click.option("--visible", default=4, show_default=True, help="Trailing chars to keep visible.")
def cmd_mask_show(src: Path, keys: tuple[str, ...], visible: int) -> None:
    """Print masked values to stdout without writing a file."""
    try:
        result = show_masked(src, keys=list(keys) or None, visible=visible)
        if not result:
            click.echo("No keys found.")
            return
        for k, v in sorted(result.items()):
            click.echo(f"{k}={v}")
    except MaskError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
