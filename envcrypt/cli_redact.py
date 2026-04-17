"""CLI commands for redacting sensitive .env values."""

from __future__ import annotations

from pathlib import Path

import click

from envcrypt.redact import RedactError, redact_file


@click.group("redact")
def redact_group() -> None:
    """Redact sensitive values from .env files."""


@redact_group.command("run")
@click.argument("src", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", default=None, help="Destination file (default: <src>.redacted)")
@click.option("-k", "--key", "keys", multiple=True, help="Explicit key names to redact")
def cmd_redact_run(src: str, output: str | None, keys: tuple[str, ...]) -> None:
    """Write a redacted copy of SRC."""
    src_path = Path(src)
    dest_path = Path(output) if output else src_path.with_suffix(".redacted")
    try:
        count = redact_file(src_path, dest_path, list(keys) if keys else None)
        click.echo(f"Redacted {count} value(s) -> {dest_path}")
    except RedactError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@redact_group.command("check")
@click.argument("src", type=click.Path(exists=True, dir_okay=False))
def cmd_redact_check(src: str) -> None:
    """List keys in SRC that would be redacted."""
    from envcrypt.redact import is_sensitive

    path = Path(src)
    flagged = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k = stripped.partition("=")[0].strip()
        if is_sensitive(k):
            flagged.append(k)

    if flagged:
        click.echo("Sensitive keys detected:")
        for k in flagged:
            click.echo(f"  {k}")
    else:
        click.echo("No sensitive keys detected.")
