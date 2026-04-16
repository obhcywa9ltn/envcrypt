"""Signing and verification of encrypted vault files using SHA-256 manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class SignError(Exception):
    pass


def get_manifest_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".envcrypt" / "manifest.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_manifest(base_dir: Path | None = None) -> dict[str, str]:
    p = get_manifest_path(base_dir)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise SignError(f"Invalid manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SignError("Manifest root must be a JSON object")
    return data


def save_manifest(manifest: dict[str, str], base_dir: Path | None = None) -> Path:
    p = get_manifest_path(base_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2))
    return p


def sign_file(file: Path, base_dir: Path | None = None) -> str:
    if not file.exists():
        raise SignError(f"File not found: {file}")
    digest = _sha256(file)
    manifest = load_manifest(base_dir)
    manifest[str(file)] = digest
    save_manifest(manifest, base_dir)
    return digest


def verify_signature(file: Path, base_dir: Path | None = None) -> bool:
    if not file.exists():
        raise SignError(f"File not found: {file}")
    manifest = load_manifest(base_dir)
    key = str(file)
    if key not in manifest:
        return False
    return manifest[key] == _sha256(file)


def remove_signature(file: Path, base_dir: Path | None = None) -> bool:
    manifest = load_manifest(base_dir)
    key = str(file)
    if key not in manifest:
        return False
    del manifest[key]
    save_manifest(manifest, base_dir)
    return True
