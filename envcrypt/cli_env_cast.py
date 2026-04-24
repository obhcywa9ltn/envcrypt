"""CLI commands for env value type-casting."""
from __future__ import annotations

import json
from pathlib import Path

import click

from envcrypt.env_cast import CastError, cast_env_file, cast_value, infer_types


@click.group("cast")
def cast_group() -> None:
    """Type-cast .env values."""


@cast_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--schema",
    "schema_json",
    default="{}",
    show_default=True,
    help="JSON object mapping key names to types (str|int|float|bool).",
)
def cmd_cast_run(env_file: Path, schema_json: str) -> None:
    """Cast values in ENV_FILE according to --schema and print as JSON."""
    try:
        schema: dict[str, str] = json.loads(schema_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid schema JSON: {exc}") from exc
    try:
        result = cast_env_file(env_file, schema)
    except CastError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(result, indent=2))


@cast_group.command("value")
@click.argument("value")
@click.argument("type", "to", type=click.Choice(["str", "int", "float", "bool"]))
def cmd_cast_value(value: str, to: str) -> None:
    """Cast a single VALUE to TYPE and print the result."""
    try:
        result = cast_value(value, to)
    except CastError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(result)


@cast_group.command("infer")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
def cmd_cast_infer(env_file: Path) -> None:
    """Infer a type schema for ENV_FILE and print it as JSON."""
    try:
        schema = infer_types(env_file)
    except CastError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(schema, indent=2))
