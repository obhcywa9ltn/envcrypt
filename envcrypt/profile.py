"""Profile management for envcrypt — named environment profiles (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

PROFILES_FILENAME = ".envcrypt_profiles.json"


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def get_profiles_path(base_dir: Optional[Path] = None) -> Path:
    """Return the path to the profiles file."""
    base = base_dir if base_dir is not None else Path.cwd()
    return base / PROFILES_FILENAME


def load_profiles(base_dir: Optional[Path] = None) -> Dict[str, str]:
    """Load profiles mapping name -> env file path.

    Returns an empty dict if the file does not exist.
    Raises ProfileError on invalid content.
    """
    path = get_profiles_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProfileError(f"Profiles file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError("Profiles file root must be a JSON object.")
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ProfileError("Each profile entry must map a string name to a string path.")
    return data


def save_profiles(profiles: Dict[str, str], base_dir: Optional[Path] = None) -> None:
    """Persist profiles to disk."""
    path = get_profiles_path(base_dir)
    path.write_text(json.dumps(profiles, indent=2), encoding="utf-8")


def add_profile(name: str, env_path: str, base_dir: Optional[Path] = None) -> Dict[str, str]:
    """Register a named profile pointing to *env_path*.

    Raises ProfileError if the name is already registered.
    """
    profiles = load_profiles(base_dir)
    if name in profiles:
        raise ProfileError(f"Profile '{name}' already exists. Use update_profile to change it.")
    profiles[name] = env_path
    save_profiles(profiles, base_dir)
    return profiles


def update_profile(name: str, env_path: str, base_dir: Optional[Path] = None) -> Dict[str, str]:
    """Update the env file path for an existing profile.

    Raises ProfileError if the profile does not exist.
    """
    profiles = load_profiles(base_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    profiles[name] = env_path
    save_profiles(profiles, base_dir)
    return profiles


def remove_profile(name: str, base_dir: Optional[Path] = None) -> Dict[str, str]:
    """Remove a profile by name.

    Raises ProfileError if the profile does not exist.
    """
    profiles = load_profiles(base_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    del profiles[name]
    save_profiles(profiles, base_dir)
    return profiles


def list_profiles(base_dir: Optional[Path] = None) -> List[str]:
    """Return a sorted list of registered profile names."""
    return sorted(load_profiles(base_dir).keys())


def get_profile(name: str, base_dir: Optional[Path] = None) -> str:
    """Return the env file path for a named profile.

    Raises ProfileError if the profile does not exist.
    """
    profiles = load_profiles(base_dir)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    return profiles[name]
