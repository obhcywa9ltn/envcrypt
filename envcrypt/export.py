"""Export and import encrypted .env files for sharing or backup."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, Optional

from envcrypt.vault import get_vault_dir, get_encrypted_path, VaultError
from envcrypt.audit import append_audit_entry


class ExportError(Exception):
    """Raised when an export or import operation fails."""


def export_env(
    name: str,
    dest: Path,
    base_dir: Optional[Path] = None,
) -> Path:
    """Copy the encrypted vault file for *name* to *dest* directory.

    Returns the path of the exported file.
    Raises ExportError if the encrypted file does not exist.
    """
    encrypted = get_encrypted_path(name, base_dir=base_dir)
    if not encrypted.exists():
        raise ExportError(f"No encrypted file found for '{name}': {encrypted}")

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out_path = dest / encrypted.name
    shutil.copy2(encrypted, out_path)

    append_audit_entry(
        {"action": "export", "name": name, "destination": str(out_path)},
        base_dir=base_dir,
    )
    return out_path


def import_env(
    src: Path,
    name: str,
    base_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> Path:
    """Copy an encrypted file from *src* into the vault under *name*.

    Returns the destination path inside the vault.
    Raises ExportError if *src* does not exist or destination exists and
    *overwrite* is False.
    """
    src = Path(src)
    if not src.exists():
        raise ExportError(f"Source file not found: {src}")

    dest = get_encrypted_path(name, base_dir=base_dir)
    if dest.exists() and not overwrite:
        raise ExportError(
            f"Encrypted file already exists for '{name}'. Use overwrite=True to replace."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

    append_audit_entry(
        {"action": "import", "name": name, "source": str(src)},
        base_dir=base_dir,
    )
    return dest


def list_exports(base_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Return a mapping of env name -> encrypted path for all vault entries."""
    vault_dir = get_vault_dir(base_dir=base_dir)
    if not vault_dir.exists():
        return {}
    return {
        p.stem: p
        for p in sorted(vault_dir.iterdir())
        if p.suffix == ".age"
    }
