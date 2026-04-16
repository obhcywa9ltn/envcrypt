"""Backup and restore encrypted vault files."""
from __future__ import annotations

import shutil
import time
from pathlib import Path


class BackupError(Exception):
    pass


def get_backup_dir(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".envcrypt" / "backups"


def create_backup(encrypted_path: Path, base_dir: Path | None = None) -> Path:
    """Copy an encrypted file into the backup directory with a timestamp suffix."""
    if not encrypted_path.exists():
        raise BackupError(f"Encrypted file not found: {encrypted_path}")

    backup_dir = get_backup_dir(base_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    dest = backup_dir / f"{encrypted_path.name}.{timestamp}.bak"
    shutil.copy2(encrypted_path, dest)
    return dest


def list_backups(name: str, base_dir: Path | None = None) -> list[Path]:
    """Return backup files for a given encrypted filename, sorted oldest-first."""
    backup_dir = get_backup_dir(base_dir)
    if not backup_dir.exists():
        return []
    matches = sorted(backup_dir.glob(f"{name}.*.bak"))
    return matches


def restore_backup(backup_path: Path, dest: Path) -> None:
    """Restore a backup file to dest."""
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, dest)


def prune_backups(name: str, keep: int = 5, base_dir: Path | None = None) -> list[Path]:
    """Delete oldest backups, keeping at most `keep` copies. Returns deleted paths."""
    if keep < 1:
        raise BackupError("keep must be >= 1")
    backups = list_backups(name, base_dir)
    to_delete = backups[: max(0, len(backups) - keep)]
    for p in to_delete:
        p.unlink()
    return to_delete
