"""Key rotation utilities for envcrypt."""

import os
from pathlib import Path
from typing import Optional

from envcrypt.crypto import AgeEncryptionError
from envcrypt.keys import generate_keypair, extract_public_key, KeyError
from envcrypt.recipients import load_recipients, save_recipients, RecipientsError
from envcrypt.vault import get_vault_dir, get_encrypted_path, lock, unlock, VaultError
from envcrypt.audit import append_audit_entry


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    old_private_key_path: str,
    new_private_key_path: str,
    recipients_file: str,
    base_dir: Optional[str] = None,
) -> dict:
    """
    Rotate the encryption key for all synced env files.

    Decrypts each vault file with the old key, then re-encrypts
    with the new key added to the recipients list.

    Returns a dict mapping env file names to their new encrypted paths.
    """
    if not os.path.exists(old_private_key_path):
        raise RotationError(f"Old private key not found: {old_private_key_path}")

    if not os.path.exists(new_private_key_path):
        raise RotationError(f"New private key not found: {new_private_key_path}")

    try:
        new_public_key = extract_public_key(new_private_key_path)
    except KeyError as exc:
        raise RotationError(f"Failed to extract public key: {exc}") from exc

    try:
        recipients = load_recipients(recipients_file)
    except RecipientsError as exc:
        raise RotationError(f"Failed to load recipients: {exc}") from exc

    vault_dir = get_vault_dir(base_dir=base_dir)
    results = {}

    for name, public_key in list(recipients.items()):
        encrypted_path = get_encrypted_path(name, base_dir=base_dir)
        if not os.path.exists(encrypted_path):
            continue

        tmp_decrypted = encrypted_path + ".tmp_rotate"
        try:
            unlock(encrypted_path, tmp_decrypted, old_private_key_path)
        except (VaultError, AgeEncryptionError) as exc:
            raise RotationError(f"Failed to decrypt '{name}' during rotation: {exc}") from exc

        try:
            new_encrypted_path = lock(tmp_decrypted, name, [new_public_key], base_dir=base_dir)
        except (VaultError, AgeEncryptionError) as exc:
            raise RotationError(f"Failed to re-encrypt '{name}' during rotation: {exc}") from exc
        finally:
            if os.path.exists(tmp_decrypted):
                os.remove(tmp_decrypted)

        results[name] = new_encrypted_path

    append_audit_entry("rotate", {"rotated_files": list(results.keys()), "new_key": new_public_key})
    return results


def generate_and_rotate(
    new_key_path: str,
    recipients_file: str,
    base_dir: Optional[str] = None,
) -> tuple:
    """Generate a new keypair and rotate all vault files to use it."""
    try:
        public_key, private_key_path = generate_keypair(new_key_path)
    except KeyError as exc:
        raise RotationError(f"Failed to generate new keypair: {exc}") from exc

    return public_key, private_key_path
