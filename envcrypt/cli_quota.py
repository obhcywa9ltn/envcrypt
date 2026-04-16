"""CLI commands for vault quota management."""

from __future__ import annotations

from pathlib import Path

import click

from envcrypt.quota import QuotaError, check_quota, load_quota, set_limit
from envcrypt.vault import get_vault_dir


@click.group("quota")
def quota_group() -> None:
    """Manage vault file quotas."""


@quota_group.command("show")
@click.option("--base-dir", default=None, help="Base directory for quota file.")
def cmd_quota_show(base_dir: str | None) -> None:
    """Show current quota usage."""
    base = Path(base_dir) if base_dir else None
    try:
        data = load_quota(base)
        limit = data.get("limit")
        vault_dir = get_vault_dir()
        count, _ = check_quota(vault_dir, base)
        click.echo(f"Usage: {count}/{limit} encrypted files")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_group.command("set")
@click.argument("limit", type=int)
@click.option("--base-dir", default=None, help="Base directory for quota file.")
def cmd_quota_set(limit: int, base_dir: str | None) -> None:
    """Set the maximum number of encrypted files allowed."""
    base = Path(base_dir) if base_dir else None
    try:
        set_limit(limit, base)
        click.echo(f"Quota limit set to {limit}.")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_group.command("check")
@click.option("--base-dir", default=None, help="Base directory for quota file.")
def cmd_quota_check(base_dir: str | None) -> None:
    """Exit non-zero if vault exceeds quota."""
    base = Path(base_dir) if base_dir else None
    try:
        vault_dir = get_vault_dir()
        count, limit = check_quota(vault_dir, base)
        click.echo(f"OK: {count}/{limit} files used.")
    except QuotaError as exc:
        click.echo(f"Quota exceeded: {exc}", err=True)
        raise SystemExit(1)
