"""Audit log for tracking encryption and sync operations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditError(Exception):
    """Raised when an audit log operation fails."""


DEFAULT_AUDIT_FILENAME = ".envcrypt_audit.json"


def get_audit_path(base_dir: str | None = None) -> Path:
    """Return the path to the audit log file."""
    base = Path(base_dir) if base_dir else Path(os.environ.get("ENVCRYPT_DIR", "."))
    return base / DEFAULT_AUDIT_FILENAME


def load_audit_log(base_dir: str | None = None) -> list[dict[str, Any]]:
    """Load existing audit log entries from disk.

    Returns an empty list if the file does not exist.
    Raises AuditError on parse failures.
    """
    path = get_audit_path(base_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuditError(f"Audit log is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise AuditError("Audit log root must be a JSON array")
    return data


def append_audit_entry(
    action: str,
    details: dict[str, Any] | None = None,
    base_dir: str | None = None,
) -> dict[str, Any]:
    """Append a new entry to the audit log and persist it.

    Returns the newly created entry.
    Raises AuditError if the log cannot be written.
    """
    entries = load_audit_log(base_dir)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "details": details or {},
    }
    entries.append(entry)
    path = get_audit_path(base_dir)
    try:
        path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except OSError as exc:
        raise AuditError(f"Failed to write audit log: {exc}") from exc
    return entry


def clear_audit_log(base_dir: str | None = None) -> None:
    """Remove all entries from the audit log by resetting it to an empty list.

    Raises AuditError if the file cannot be written.
    """
    path = get_audit_path(base_dir)
    try:
        path.write_text(json.dumps([]), encoding="utf-8")
    except OSError as exc:
        raise AuditError(f"Failed to clear audit log: {exc}") from exc
