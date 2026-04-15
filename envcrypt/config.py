"""Project-level configuration management for envcrypt."""

import json
import os
from pathlib import Path
from typing import Any

CONFIG_FILENAME = ".envcrypt.json"


class ConfigError(Exception):
    """Raised when a configuration operation fails."""


def get_config_path(base_dir: Path | None = None) -> Path:
    """Return the path to the project config file.

    Args:
        base_dir: Directory to look in. Defaults to current working directory.

    Returns:
        Path to the config file.
    """
    root = base_dir if base_dir is not None else Path(os.getcwd())
    return root / CONFIG_FILENAME


def load_config(base_dir: Path | None = None) -> dict[str, Any]:
    """Load the project config from disk.

    Returns an empty dict if the file does not exist.

    Args:
        base_dir: Directory to look in. Defaults to current working directory.

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigError: If the file exists but cannot be parsed.
    """
    config_path = get_config_path(base_dir)
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config file root must be a JSON object.")
    return data


def save_config(config: dict[str, Any], base_dir: Path | None = None) -> Path:
    """Persist the configuration dictionary to disk.

    Args:
        config: Configuration data to save.
        base_dir: Directory to write to. Defaults to current working directory.

    Returns:
        Path where the config was written.

    Raises:
        ConfigError: If the file cannot be written.
    """
    config_path = get_config_path(base_dir)
    try:
        with config_path.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
    except OSError as exc:
        raise ConfigError(f"Could not write config file: {exc}") from exc
    return config_path


def set_config_value(key: str, value: Any, base_dir: Path | None = None) -> None:
    """Set a single key in the project config, persisting immediately.

    Args:
        key: Top-level key to set.
        value: Value to assign.
        base_dir: Directory to use. Defaults to current working directory.
    """
    config = load_config(base_dir)
    config[key] = value
    save_config(config, base_dir)


def get_config_value(key: str, default: Any = None, base_dir: Path | None = None) -> Any:
    """Retrieve a single key from the project config.

    Args:
        key: Top-level key to retrieve.
        default: Value to return when key is absent.
        base_dir: Directory to use. Defaults to current working directory.

    Returns:
        The stored value, or *default* if the key is missing.
    """
    config = load_config(base_dir)
    return config.get(key, default)
