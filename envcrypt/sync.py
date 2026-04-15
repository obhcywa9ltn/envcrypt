"""Sync encrypted .env files for all recipients in the project."""

import os
from pathlib import Path
from typing import Optional

from envcrypt.recipients import load_recipients, RecipientsError
from envcrypt.vault import get_vault_dir, get_encrypted_path, lock, VaultError
from envcrypt.crypto import AgeEncryptionError


class SyncError(Exception):
    """Raised when a sync operation fails."""


def sync_env_file(
    env_file: str,
    base: Optional[str] = None,
    recipients_file: Optional[str] = None,
) -> dict[str, str]:
    """Encrypt *env_file* for every recipient and write to the vault.

    Returns a mapping of {recipient_name: encrypted_file_path} for all
    successfully written files.

    Raises SyncError on any failure so callers get a single exception type.
    """
    env_path = Path(env_file)
    if not env_path.exists():
        raise SyncError(f"env file not found: {env_file}")

    try:
        recipients = load_recipients(recipients_file)
    except RecipientsError as exc:
        raise SyncError(f"failed to load recipients: {exc}") from exc

    if not recipients:
        raise SyncError("no recipients configured — run 'envcrypt add' first")

    results: dict[str, str] = {}

    for name, public_key in recipients.items():
        try:
            out_path = get_encrypted_path(name, base=base)
            lock(str(env_path), str(out_path), public_key)
            results[name] = str(out_path)
        except (VaultError, AgeEncryptionError) as exc:
            raise SyncError(f"failed to encrypt for recipient '{name}': {exc}") from exc

    return results


def list_synced_files(base: Optional[str] = None) -> list[str]:
    """Return paths of all encrypted files currently in the vault directory."""
    vault_dir = Path(get_vault_dir(base=base))
    if not vault_dir.exists():
        return []
    return sorted(str(p) for p in vault_dir.rglob("*.age"))
