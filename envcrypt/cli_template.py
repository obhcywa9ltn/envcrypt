"""CLI commands for .env template generation and application."""

from __future__ import annotations

from pathlib import Path

import click

from envcrypt.template import TemplateError, generate_template, apply_template
from envcrypt.keys import get_key_file


@click.group("template")
def template_group() -> None:
    """Generate and apply .env templates."""


@template_group.command("generate")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Destination path for the template (default: <env_file>.example).",
)
def cmd_template_generate(env_file: Path, dest: Path | None) -> None:
    """Generate a .env.example template from ENV_FILE with values redacted."""
    try:
        out = generate_template(env_file, dest=dest)
        click.echo(f"Template written to {out}")
    except TemplateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@template_group.command("apply")
@click.argument("template_file", type=click.Path(exists=True, path_type=Path))
@click.argument("dest", type=click.Path(path_type=Path))
@click.option(
    "--set",
    "pairs",
    multiple=True,
    metavar="KEY=VALUE",
    help="Key/value pairs to inject (may be repeated).",
)
def cmd_template_apply(template_file: Path, dest: Path, pairs: tuple[str, ...]) -> None:
    """Apply values to TEMPLATE_FILE and write the result to DEST."""
    values: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            click.echo(f"Error: invalid pair '{pair}' — expected KEY=VALUE", err=True)
            raise SystemExit(1)
        k, v = pair.split("=", 1)
        values[k] = v

    try:
        out = apply_template(template_file, values, dest)
        click.echo(f"Populated env written to {out}")
    except TemplateError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
