"""Vault management: encrypt/decrypt .env files into/from a vault directory."""

from __future__ import annotations

import os
from pathlib import Path

from envcrypt.crypto import AgeEncryptionError, encrypt_file, decrypt_file
from envcrypt.recipients import RecipientsError, load_recipients


class VaultError(Exception):
    """Raised when a vault operation fails."""


DEFAULT_VAULT_DIR = ".envcrypt"
DEFAULT_ENV_FILE = ".env"


def get_vault_dir(base: str | Path | None = None) -> Path:
    """Return the vault directory, using ENVCRYPT_VAULT_DIR env var as override."""
    override = os.environ.get("ENVCRYPT_VAULT_DIR")
    if override:
        return Path(override)
    if base is not None:
        return Path(base) / DEFAULT_VAULT_DIR
    return Path.cwd() / DEFAULT_VAULT_DIR


def get_encrypted_path(env_file: str | Path, vault_dir: str | Path | None = None) -> Path:
    """Return the path where an encrypted .env file will be stored in the vault."""
    env_path = Path(env_file)
    vdir = get_vault_dir() if vault_dir is None else Path(vault_dir)
    return vdir / (env_path.name + ".age")


def lock(env_file: str | Path, recipients_file: str | Path, vault_dir: str | Path | None = None) -> Path:
    """Encrypt *env_file* for all recipients and store it in the vault.

    Returns the path of the encrypted output file.
    Raises VaultError on any failure.
    """
    env_path = Path(env_file)
    if not env_path.exists():
        raise VaultError(f"env file not found: {env_path}")

    try:
        recipients = load_recipients(recipients_file)
    except RecipientsError as exc:
        raise VaultError(f"failed to load recipients: {exc}") from exc

    if not recipients:
        raise VaultError("no recipients configured — add at least one public key")

    public_keys = list(recipients.values())
    vdir = get_vault_dir() if vault_dir is None else Path(vault_dir)
    vdir.mkdir(parents=True, exist_ok=True)
    output_path = get_encrypted_path(env_path, vdir)

    try:
        encrypt_file(str(env_path), str(output_path), public_keys)
    except AgeEncryptionError as exc:
        raise VaultError(f"encryption failed: {exc}") from exc

    return output_path


def unlock(encrypted_file: str | Path, identity_file: str | Path, output: str | Path | None = None) -> Path:
    """Decrypt *encrypted_file* using *identity_file* and write the plaintext.

    Returns the path of the decrypted output file.
    Raises VaultError on any failure.
    """
    enc_path = Path(encrypted_file)
    if not enc_path.exists():
        raise VaultError(f"encrypted file not found: {enc_path}")

    if output is None:
        stem = enc_path.stem  # strips .age
        out_path = Path.cwd() / stem
    else:
        out_path = Path(output)

    try:
        decrypt_file(str(enc_path), str(out_path), str(identity_file))
    except AgeEncryptionError as exc:
        raise VaultError(f"decryption failed: {exc}") from exc

    return out_path
