"""Key management utilities for age encryption."""

import os
import subprocess
from pathlib import Path
from typing import Optional

DEFAULT_KEY_DIR = Path.home() / ".config" / "envcrypt"
DEFAULT_KEY_FILE = DEFAULT_KEY_DIR / "key.txt"


class KeyError(Exception):
    """Raised when a key operation fails."""
    pass


def get_key_dir() -> Path:
    """Return the directory used to store age keys."""
    key_dir = os.environ.get("ENVCRYPT_KEY_DIR")
    if key_dir:
        return Path(key_dir)
    return DEFAULT_KEY_DIR


def get_key_file() -> Path:
    """Return the path to the age private key file."""
    key_file = os.environ.get("ENVCRYPT_KEY_FILE")
    if key_file:
        return Path(key_file)
    return get_key_dir() / "key.txt"


def generate_keypair(key_file: Optional[Path] = None) -> str:
    """Generate a new age keypair and save the private key.

    Returns the public key string.
    Raises KeyError if key generation fails.
    """
    if key_file is None:
        key_file = get_key_file()

    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        raise KeyError(f"Key file already exists: {key_file}")

    try:
        result = subprocess.run(
            ["age-keygen", "-o", str(key_file)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise KeyError("age-keygen not found. Please install age.")

    if result.returncode != 0:
        raise KeyError(f"Key generation failed: {result.stderr.strip()}")

    return extract_public_key(key_file)


def extract_public_key(key_file: Optional[Path] = None) -> str:
    """Extract the public key from an age private key file.

    Returns the public key string.
    Raises KeyError if extraction fails.
    """
    if key_file is None:
        key_file = get_key_file()

    if not key_file.exists():
        raise KeyError(f"Key file not found: {key_file}")

    with open(key_file, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# public key:"):
                return line.split(":", 1)[1].strip()

    raise KeyError(f"No public key found in {key_file}")


def key_exists(key_file: Optional[Path] = None) -> bool:
    """Return True if the age key file exists."""
    if key_file is None:
        key_file = get_key_file()
    return key_file.exists()
