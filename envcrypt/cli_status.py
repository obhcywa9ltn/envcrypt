"""CLI command for displaying vault status."""

from __future__ import annotations

import click

from envcrypt.status import StatusError, get_vault_status


@click.command("status")
@click.option(
    "--base-dir",
    default=None,
    help="Base directory to resolve vault and .env paths from.",
    type=click.Path(exists=False, file_okay=False),
)
def cmd_status(base_dir: str | None) -> None:
    """Show sync status of all tracked .env files."""
    from pathlib import Path

    base = Path(base_dir) if base_dir else None

    try:
        vault_status = get_vault_status(base_dir=base)
    except StatusError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not vault_status.tracked:
        click.echo("No tracked .env files found.")
        return

    col_w = max(len(f.name) for f in vault_status.tracked) + 2

    click.echo(f"{'NAME':<{col_w}}  {'ENV':^6}  {'VAULT':^6}  {'STATUS'}")
    click.echo("-" * (col_w + 28))

    for fs in vault_status.tracked:
        env_mark = "yes" if fs.env_exists else "no "
        enc_mark = "yes" if fs.encrypted_exists else "no "
        if fs.in_sync:
            status_label = click.style("in sync", fg="green")
        elif not fs.encrypted_exists:
            status_label = click.style("not locked", fg="yellow")
        elif not fs.env_exists:
            status_label = click.style("not unlocked", fg="cyan")
        else:
            status_label = click.style("out of sync", fg="red")

        click.echo(f"{fs.name:<{col_w}}  {env_mark:^6}  {enc_mark:^6}  {status_label}")

    click.echo()
    if vault_status.all_in_sync:
        click.echo(click.style("All files are in sync.", fg="green"))
    else:
        click.echo(click.style("Some files are out of sync.", fg="yellow"))
