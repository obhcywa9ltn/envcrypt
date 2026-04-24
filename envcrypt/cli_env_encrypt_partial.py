"""CLI commands for partial (inline) encryption of .env files."""
from __future__ import annotations

from pathlib import Path

import click

from envcrypt.env_encrypt_partial import PartialEncryptError, encrypt_keys, list_encrypted_keys
from envcrypt.recipients import load_recipients, RecipientsError


@click.group("partial")
def partial_group() -> None:
    """Partially encrypt individual keys inside a .env file."""


@partial_group.command("encrypt")
@click.argument("env_file", type=click.Path(path_type=Path))
@click.option("-k", "--key", "keys", multiple=True, required=True, help="Key(s) to encrypt.")
@click.option("-r", "--recipient", "recipients", multiple=True, help="age recipient public key.")
@click.option("-R", "--recipients-file", "recipients_file", default=None, type=click.Path(path_type=Path), help="Path to recipients JSON file.")
@click.option("-o", "--output", "dest", default=None, type=click.Path(path_type=Path), help="Output file (defaults to in-place).")
def cmd_partial_encrypt(
    env_file: Path,
    keys: tuple,
    recipients: tuple,
    recipients_file: Path | None,
    dest: Path | None,
) -> None:
    """Encrypt specific KEY(s) inside ENV_FILE in-place."""
    all_recipients = list(recipients)
    if recipients_file:
        try:
            loaded = load_recipients(recipients_file)
            all_recipients.extend(loaded.values())
        except RecipientsError as exc:
            raise click.ClickException(str(exc)) from exc
    try:
        mapping = encrypt_keys(env_file, list(keys), all_recipients, dest=dest)
    except PartialEncryptError as exc:
        raise click.ClickException(str(exc)) from exc
    for k in mapping:
        click.echo(f"encrypted: {k}")


@partial_group.command("ls")
@click.argument("env_file", type=click.Path(path_type=Path))
def cmd_partial_ls(env_file: Path) -> None:
    """List keys that are already partially encrypted in ENV_FILE."""
    try:
        keys = list_encrypted_keys(env_file)
    except PartialEncryptError as exc:
        raise click.ClickException(str(exc)) from exc
    if not keys:
        click.echo("no encrypted keys")
    else:
        for k in keys:
            click.echo(k)
