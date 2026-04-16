"""Snapshot support: capture and restore vault state at a point in time."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List


class SnapshotError(Exception):
    pass


def get_snapshot_dir(base_dir: Path | None = None) -> Path:
    root = base_dir or Path.cwd()
    return root / ".envcrypt" / "snapshots"


@dataclass
class SnapshotMeta:
    name: str
    created_at: str
    files: List[str] = field(default_factory=list)


def _meta_path(snapshot_dir: Path, name: str) -> Path:
    return snapshot_dir / name / "meta.json"


def create_snapshot(name: str, vault_dir: Path, base_dir: Path | None = None) -> Path:
    if not vault_dir.exists():
        raise SnapshotError(f"Vault directory not found: {vault_dir}")
    snapshot_dir = get_snapshot_dir(base_dir)
    dest = snapshot_dir / name
    if dest.exists():
        raise SnapshotError(f"Snapshot '{name}' already exists")
    dest.mkdir(parents=True)
    copied: list[str] = []
    for f in vault_dir.rglob("*.age"):
        rel = f.relative_to(vault_dir)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        copied.append(str(rel))
    meta = SnapshotMeta(name=name, created_at=datetime.now(timezone.utc).isoformat(), files=copied)
    _meta_path(snapshot_dir, name).write_text(json.dumps(meta.__dict__, indent=2))
    return dest


def list_snapshots(base_dir: Path | None = None) -> list[SnapshotMeta]:
    snapshot_dir = get_snapshot_dir(base_dir)
    if not snapshot_dir.exists():
        return []
    results = []
    for meta_file in sorted(snapshot_dir.glob("*/meta.json")):
        data = json.loads(meta_file.read_text())
        results.append(SnapshotMeta(**data))
    return results


def restore_snapshot(name: str, vault_dir: Path, base_dir: Path | None = None) -> list[str]:
    snapshot_dir = get_snapshot_dir(base_dir)
    src = snapshot_dir / name
    if not src.exists():
        raise SnapshotError(f"Snapshot '{name}' not found")
    vault_dir.mkdir(parents=True, exist_ok=True)
    restored: list[str] = []
    for f in src.rglob("*.age"):
        rel = f.relative_to(src)
        target = vault_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        restored.append(str(rel))
    return restored


def delete_snapshot(name: str, base_dir: Path | None = None) -> None:
    snapshot_dir = get_snapshot_dir(base_dir)
    dest = snapshot_dir / name
    if not dest.exists():
        raise SnapshotError(f"Snapshot '{name}' not found")
    shutil.rmtree(dest)
