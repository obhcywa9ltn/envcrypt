"""Diff utilities for comparing local .env files against encrypted vault contents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Set, Tuple

from envcrypt.vault import VaultError, get_encrypted_path, unlock


class DiffError(Exception):
    """Raised when a diff operation fails."""


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file into a key/value dict, ignoring comments and blanks."""
    result: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def diff_env(
    env_file: str | Path,
    key_file: str | Path,
    base: str = "default",
    vault_dir: str | Path | None = None,
) -> Tuple[Set[str], Set[str], Dict[str, Tuple[str, str]]]:
    """Compare a local .env file against its decrypted vault counterpart.

    Returns a tuple of:
        added   – keys present locally but not in vault
        removed – keys present in vault but not locally
        changed – keys whose values differ {key: (local_val, vault_val)}

    Raises DiffError on any failure.
    """
    env_path = Path(env_file)
    if not env_path.exists():
        raise DiffError(f"Local env file not found: {env_path}")

    try:
        encrypted_path = get_encrypted_path(str(env_path), base=base, vault_dir=vault_dir)
    except VaultError as exc:
        raise DiffError(str(exc)) from exc

    if not Path(encrypted_path).exists():
        raise DiffError(f"No encrypted counterpart found at: {encrypted_path}")

    import tempfile

    try:
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False) as tmp:
            tmp_path = tmp.name
        unlock(encrypted_path, tmp_path, str(key_file))
        vault_vars = _parse_env_file(Path(tmp_path))
    except VaultError as exc:
        raise DiffError(f"Failed to decrypt vault file: {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    local_vars = _parse_env_file(env_path)

    local_keys = set(local_vars)
    vault_keys = set(vault_vars)

    added = local_keys - vault_keys
    removed = vault_keys - local_keys
    changed: Dict[str, Tuple[str, str]] = {
        k: (local_vars[k], vault_vars[k])
        for k in local_keys & vault_keys
        if local_vars[k] != vault_vars[k]
    }

    return added, removed, changed
