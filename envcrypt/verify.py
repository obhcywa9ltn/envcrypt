"""Verify integrity of encrypted vault files against their source .env files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envcrypt.vault import get_encrypted_path, VaultError
from envcrypt.crypto import decrypt_file, AgeEncryptionError


class VerifyError(Exception):
    """Raised when verification fails unexpectedly."""


@dataclass
class VerifyResult:
    env_file: Path
    encrypted_file: Path
    match: bool
    reason: Optional[str] = None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def verify_env_file(
    env_file: Path,
    key_file: Path,
    vault_dir: Optional[Path] = None,
    base: Optional[Path] = None,
) -> VerifyResult:
    """Decrypt the vault copy and compare it byte-for-byte with *env_file*.

    Returns a :class:`VerifyResult` describing whether the files match.
    Raises :class:`VerifyError` on unexpected I/O or decryption problems.
    """
    if not env_file.exists():
        raise VerifyError(f"env file not found: {env_file}")

    try:
        encrypted_path = get_encrypted_path(env_file.name, vault_dir=vault_dir, base=base)
    except VaultError as exc:
        raise VerifyError(str(exc)) from exc

    if not encrypted_path.exists():
        return VerifyResult(
            env_file=env_file,
            encrypted_file=encrypted_path,
            match=False,
            reason="encrypted file does not exist",
        )

    tmp_dir = encrypted_path.parent / ".verify_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_out = tmp_dir / env_file.name

    try:
        try:
            decrypt_file(encrypted_path, tmp_out, key_file)
        except AgeEncryptionError as exc:
            return VerifyResult(
                env_file=env_file,
                encrypted_file=encrypted_path,
                match=False,
                reason=f"decryption failed: {exc}",
            )

        match = _sha256(env_file) == _sha256(tmp_out)
        return VerifyResult(
            env_file=env_file,
            encrypted_file=encrypted_path,
            match=match,
            reason=None if match else "content differs",
        )
    finally:
        if tmp_out.exists():
            tmp_out.unlink()
        try:
            tmp_dir.rmdir()
        except OSError:
            pass
