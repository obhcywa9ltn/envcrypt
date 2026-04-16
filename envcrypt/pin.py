"""Pin management: lock a vault to a specific encrypted snapshot hash."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PIN_FILENAME = ".envcrypt_pins.json"


class PinError(Exception):
    pass


def get_pins_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / PIN_FILENAME


def load_pins(base_dir: Path | None = None) -> dict[str, str]:
    path = get_pins_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PinError(f"Invalid pins file: {exc}") from exc
    if not isinstance(data, dict):
        raise PinError("Pins file root must be a JSON object")
    return data


def save_pins(pins: dict[str, str], base_dir: Path | None = None) -> None:
    path = get_pins_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pins, indent=2))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def pin_file(name: str, encrypted_path: Path, base_dir: Path | None = None) -> str:
    """Record the current hash of an encrypted file under *name*."""
    if not encrypted_path.exists():
        raise PinError(f"Encrypted file not found: {encrypted_path}")
    digest = _sha256(encrypted_path)
    pins = load_pins(base_dir)
    pins[name] = digest
    save_pins(pins, base_dir)
    return digest


def check_pin(name: str, encrypted_path: Path, base_dir: Path | None = None) -> bool:
    """Return True if *encrypted_path* matches the stored pin for *name*."""
    pins = load_pins(base_dir)
    if name not in pins:
        raise PinError(f"No pin found for '{name}'")
    if not encrypted_path.exists():
        return False
    return _sha256(encrypted_path) == pins[name]


def remove_pin(name: str, base_dir: Path | None = None) -> bool:
    """Remove a pin entry; returns True if it existed."""
    pins = load_pins(base_dir)
    if name not in pins:
        return False
    del pins[name]
    save_pins(pins, base_dir)
    return True
