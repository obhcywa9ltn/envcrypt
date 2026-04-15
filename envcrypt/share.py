"""Secure sharing of encrypted .env files with specific recipients."""

from __future__ import annotations

import shutil
from pathlib import Path

from envcrypt.crypto import encrypt_file, decrypt_file, AgeEncryptionError
from envcrypt.recipients import load_recipients, RecipientsError
from envcrypt.vault import get_vault_dir, get_encrypted_path, VaultError


class ShareError(Exception):
    """Raised when a share operation fails."""


def share_with(
    env_file: Path,
    recipient_names: list[str],
    dest_dir: Path,
    base_dir: Path | None = None,
) -> dict[str, Path]:
    """Encrypt *env_file* for a subset of recipients and write outputs to *dest_dir*.

    Returns a mapping of recipient name -> output path.
    """
    if not env_file.exists():
        raise ShareError(f"env file not found: {env_file}")

    try:
        all_recipients = load_recipients(base_dir=base_dir)
    except RecipientsError as exc:
        raise ShareError(str(exc)) from exc

    missing = [n for n in recipient_names if n not in all_recipients]
    if missing:
        raise ShareError(f"unknown recipients: {', '.join(missing)}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Path] = {}

    for name in recipient_names:
        public_key = all_recipients[name]
        out_path = dest_dir / f"{env_file.stem}.{name}.age"
        try:
            encrypt_file(env_file, out_path, recipients=[public_key])
        except AgeEncryptionError as exc:
            raise ShareError(f"encryption failed for {name}: {exc}") from exc
        results[name] = out_path

    return results


def receive_share(
    shared_file: Path,
    private_key_file: Path,
    dest: Path,
) -> Path:
    """Decrypt a shared file using *private_key_file* and write to *dest*."""
    if not shared_file.exists():
        raise ShareError(f"shared file not found: {shared_file}")
    if not private_key_file.exists():
        raise ShareError(f"private key not found: {private_key_file}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        decrypt_file(shared_file, dest, identity=private_key_file)
    except AgeEncryptionError as exc:
        raise ShareError(f"decryption failed: {exc}") from exc
    return dest


def list_shares(dest_dir: Path) -> list[Path]:
    """Return all .age share files found in *dest_dir*."""
    if not dest_dir.exists():
        return []
    return sorted(dest_dir.glob("*.age"))
