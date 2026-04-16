"""Quota tracking: limit number of encrypted files per vault."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_QUOTA = 50
QUOTA_FILENAME = ".envcrypt_quota.json"


class QuotaError(Exception):
    pass


def get_quota_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / QUOTA_FILENAME


def load_quota(base_dir: Path | None = None) -> dict:
    path = get_quota_path(base_dir)
    if not path.exists():
        return {"limit": DEFAULT_QUOTA}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise QuotaError(f"Invalid quota file: {exc}") from exc
    if not isinstance(data, dict):
        raise QuotaError("Quota file must be a JSON object")
    return data


def save_quota(data: dict, base_dir: Path | None = None) -> None:
    path = get_quota_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def set_limit(limit: int, base_dir: Path | None = None) -> None:
    if limit < 1:
        raise QuotaError("Limit must be a positive integer")
    data = load_quota(base_dir)
    data["limit"] = limit
    save_quota(data, base_dir)


def check_quota(vault_dir: Path, base_dir: Path | None = None) -> tuple[int, int]:
    """Return (current_count, limit). Raises QuotaError if exceeded."""
    data = load_quota(base_dir)
    limit = data.get("limit", DEFAULT_QUOTA)
    if not vault_dir.exists():
        return 0, limit
    count = len(list(vault_dir.glob("*.age")))
    if count > limit:
        raise QuotaError(
            f"Vault exceeds quota: {count} files found, limit is {limit}"
        )
    return count, limit
