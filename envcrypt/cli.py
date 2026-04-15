"""Command-line interface for envcrypt."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envcrypt.keys import KeyError as EnvKeyError, generate_keypair, get_key_file
from envcrypt.recipients import RecipientsError, add_recipient, load_recipients
from envcrypt.vault import VaultError, lock, unlock

RECIPIENTS_FILE = "envcrypt-recipients.json"


@click.group()
def cli() -> None:
    """envcrypt — encrypt and sync .env files with age."""


@cli.command("init")
def cmd_init() -> None:
    """Generate a new age keypair for the current user."""
    try:
        pub, priv = generate_keypair()
    except EnvKeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Public key : {pub}")
    click.echo(f"Private key: {priv}")
    click.echo("Keys stored in the envcrypt key directory.")


@cli.command("add")
@click.argument("name")
@click.argument("public_key")
@click.option("--recipients", default=RECIPIENTS_FILE, show_default=True, help="Recipients file path.")
def cmd_add(name: str, public_key: str, recipients: str) -> None:
    """Add a recipient NAME with PUBLIC_KEY to the recipients file."""
    try:
        add_recipient(recipients, name, public_key)
    except RecipientsError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Added recipient '{name}'.")


@cli.command("list")
@click.option("--recipients", default=RECIPIENTS_FILE, show_default=True, help="Recipients file path.")
def cmd_list(recipients: str) -> None:
    """List all configured recipients."""
    try:
        data = load_recipients(recipients)
    except RecipientsError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    if not data:
        click.echo("No recipients configured.")
        return
    for name, key in data.items():
        click.echo(f"  {name}: {key}")


@cli.command("lock")
@click.argument("env_file", default=".env")
@click.option("--recipients", default=RECIPIENTS_FILE, show_default=True, help="Recipients file path.")
@click.option("--vault-dir", default=None, help="Override vault directory.")
def cmd_lock(env_file: str, recipients: str, vault_dir: str | None) -> None:
    """Encrypt ENV_FILE into the vault for all recipients."""
    try:
        out = lock(env_file, recipients, vault_dir=vault_dir)
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Encrypted → {out}")


@cli.command("unlock")
@click.argument("encrypted_file", default=".envcrypt/.env.age")
@click.option("--identity", default=None, help="Path to age identity (private key) file.")
@click.option("--output", default=None, help="Output path for decrypted file.")
def cmd_unlock(encrypted_file: str, identity: str | None, output: str | None) -> None:
    """Decrypt ENCRYPTED_FILE using your age identity."""
    if identity is None:
        try:
            identity = str(get_key_file())
        except EnvKeyError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)
    try:
        out = unlock(encrypted_file, identity, output=output)
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Decrypted → {out}")


if __name__ == "__main__":
    cli()
