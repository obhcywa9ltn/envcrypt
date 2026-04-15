"""Status reporting for envcrypt: compare local .env files against the vault."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envcrypt.vault import get_vault_dir, get_encrypted_path
from envcrypt.sync import list_synced_files


class StatusError(Exception):
    """Raised when status reporting fails."""


@dataclass
class FileStatus:
    name: str
    env_path: Path
    encrypted_path: Path
    env_exists: bool
    encrypted_exists: bool
    in_sync: bool  # True when both exist and encrypted is newer than env


@dataclass
class VaultStatus:
    tracked: List[FileStatus] = field(default_factory=list)

    @property
    def all_in_sync(self) -> bool:
        return all(f.in_sync for f in self.tracked)


def _file_status(name: str, env_path: Path, enc_path: Path) -> FileStatus:
    env_exists = env_path.exists()
    enc_exists = enc_path.exists()

    if env_exists and enc_exists:
        env_mtime = env_path.stat().st_mtime
        enc_mtime = enc_path.stat().st_mtime
        in_sync = enc_mtime >= env_mtime
    else:
        in_sync = False

    return FileStatus(
        name=name,
        env_path=env_path,
        encrypted_path=enc_path,
        env_exists=env_exists,
        encrypted_exists=enc_exists,
        in_sync=in_sync,
    )


def get_vault_status(base_dir: Path | None = None) -> VaultStatus:
    """Return the status of all tracked .env files relative to the vault."""
    vault_dir = get_vault_dir(base_dir=base_dir)

    try:
        synced = list_synced_files(base_dir=base_dir)
    except Exception as exc:  # pragma: no cover
        raise StatusError(f"Could not list synced files: {exc}") from exc

    statuses: List[FileStatus] = []
    for name, env_path_str in synced.items():
        env_path = Path(env_path_str)
        enc_path = get_encrypted_path(name, vault_dir=vault_dir)
        statuses.append(_file_status(name, env_path, enc_path))

    return VaultStatus(tracked=statuses)
