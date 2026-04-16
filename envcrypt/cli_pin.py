"""CLI commands for vault pinning."""
import click
from pathlib import Path
from envcrypt.pin import PinError, pin_file, check_pin, remove_pin, load_pins
from envcrypt.vault import get_encrypted_path, get_vault_dir


@click.group("pin")
def pin_group() -> None:
    """Pin encrypted vault snapshots by hash."""


@pin_group.command("set")
@click.argument("name")
@click.option("--base", default=None, help="Override for .env file base name")
def cmd_pin_set(name: str, base: str | None) -> None:
    """Pin the current encrypted snapshot for NAME."""
    try:
        vault_dir = get_vault_dir()
        enc_path = get_encrypted_path(base or name, vault_dir)
        digest = pin_file(name, enc_path)
        click.echo(f"Pinned '{name}' → {digest[:16]}...")
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_group.command("check")
@click.argument("name")
@click.option("--base", default=None)
def cmd_pin_check(name: str, base: str | None) -> None:
    """Check whether the current snapshot matches the stored pin."""
    try:
        vault_dir = get_vault_dir()
        enc_path = get_encrypted_path(base or name, vault_dir)
        ok = check_pin(name, enc_path)
        if ok:
            click.echo(f"OK: '{name}' matches pin.")
        else:
            click.echo(f"MISMATCH: '{name}' does not match pin.", err=True)
            raise SystemExit(1)
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_group.command("remove")
@click.argument("name")
def cmd_pin_remove(name: str) -> None:
    """Remove the stored pin for NAME."""
    try:
        removed = remove_pin(name)
        if removed:
            click.echo(f"Removed pin for '{name}'.")
        else:
            click.echo(f"No pin found for '{name}'.")
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_group.command("list")
def cmd_pin_list() -> None:
    """List all stored pins."""
    try:
        pins = load_pins()
        if not pins:
            click.echo("No pins stored.")
            return
        for name, digest in pins.items():
            click.echo(f"{name}: {digest[:16]}...")
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
