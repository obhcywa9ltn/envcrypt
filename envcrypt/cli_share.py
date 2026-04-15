"""CLI commands for secure sharing of encrypted .env files."""

from __future__ import annotations

from pathlib import Path

import click

from envcrypt.share import ShareError, share_with, receive_share, list_shares


@click.group(name="share")
def share_group() -> None:
    """Share encrypted env files with specific recipients."""


@share_group.command("push")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("recipients", nargs=-1, required=True)
@click.option("--dest", default=".envcrypt/shares", show_default=True,
              type=click.Path(path_type=Path), help="Output directory for share files.")
def cmd_share_push(env_file: Path, recipients: tuple[str, ...], dest: Path) -> None:
    """Encrypt ENV_FILE for one or more named RECIPIENTS."""
    try:
        result = share_with(env_file, list(recipients), dest)
    except ShareError as exc:
        raise click.ClickException(str(exc)) from exc

    for name, path in result.items():
        click.echo(f"Shared with {name}: {path}")


@share_group.command("pull")
@click.argument("shared_file", type=click.Path(exists=True, path_type=Path))
@click.argument("dest", type=click.Path(path_type=Path))
@click.option("--key", "key_file", required=True,
              type=click.Path(path_type=Path), help="Path to your age private key.")
def cmd_share_pull(shared_file: Path, dest: Path, key_file: Path) -> None:
    """Decrypt SHARED_FILE using your private key and write to DEST."""
    try:
        out = receive_share(shared_file, key_file, dest)
    except ShareError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Decrypted to {out}")


@share_group.command("ls")
@click.option("--dir", "share_dir", default=".envcrypt/shares", show_default=True,
              type=click.Path(path_type=Path), help="Directory to list share files from.")
def cmd_share_ls(share_dir: Path) -> None:
    """List all share files in the shares directory."""
    files = list_shares(share_dir)
    if not files:
        click.echo("No share files found.")
        return
    for f in files:
        click.echo(str(f))
