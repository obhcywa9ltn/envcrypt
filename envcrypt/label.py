"""Label management for tagged grouping of vault files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class LabelError(Exception):
    pass


def get_labels_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".envcrypt" / "labels.json"


def load_labels(base_dir: Path | None = None) -> Dict[str, List[str]]:
    path = get_labels_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise LabelError(f"Invalid labels file: {exc}") from exc
    if not isinstance(data, dict):
        raise LabelError("Labels file must be a JSON object")
    return data


def save_labels(labels: Dict[str, List[str]], base_dir: Path | None = None) -> None:
    path = get_labels_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=2))


def add_label(name: str, files: List[str], base_dir: Path | None = None) -> Dict[str, List[str]]:
    labels = load_labels(base_dir)
    if name in labels:
        raise LabelError(f"Label '{name}' already exists")
    labels[name] = list(files)
    save_labels(labels, base_dir)
    return labels


def remove_label(name: str, base_dir: Path | None = None) -> Dict[str, List[str]]:
    labels = load_labels(base_dir)
    if name not in labels:
        raise LabelError(f"Label '{name}' not found")
    del labels[name]
    save_labels(labels, base_dir)
    return labels


def get_label(name: str, base_dir: Path | None = None) -> List[str]:
    labels = load_labels(base_dir)
    if name not in labels:
        raise LabelError(f"Label '{name}' not found")
    return labels[name]
