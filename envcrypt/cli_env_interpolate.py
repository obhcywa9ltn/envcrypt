"""CLI commands for env variable interpolation."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_interpolate import InterpolateError, interpolate_env_file, list_references


@click.group("interpolate")
def interpolate_group() -> None:
    """Interpolate variable references inside .env files."""


@interpolate_group.command("run")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--dest", type=click.Path(path_type=Path), default=None,
              help="Output path (default: <src>.interpolated<ext>)")
@click.option("--set", "extra", multiple=True, metavar="KEY=VALUE",
              help="Extra context variables (may be repeated)")
def cmd_interpolate_run(src: Path, dest: Path | None, extra: tuple) -> None:
    """Resolve all $VAR / ${VAR} references in SRC and write to DEST."""
    extra_context: dict = {}
    for item in extra:
        if "=" not in item:
            click.echo(f"Invalid --set value (expected KEY=VALUE): {item}", err=True)
            raise SystemExit(1)
        k, _, v = item.partition("=")
        extra_context[k] = v

    try:
        resolved = interpolate_env_file(src, dest, extra_context=extra_context)
        out = dest or src.with_suffix(".interpolated" + src.suffix)
        click.echo(f"Interpolated {len(resolved)} key(s) -> {out}")
    except InterpolateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@interpolate_group.command("refs")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
def cmd_interpolate_refs(src: Path) -> None:
    """List all variable references found in SRC."""
    try:
        refs = list_references(src)
    except InterpolateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    has_refs = False
    for key, names in refs.items():
        if names:
            has_refs = True
            click.echo(f"{key}: {', '.join(names)}")
    if not has_refs:
        click.echo("No variable references found.")
