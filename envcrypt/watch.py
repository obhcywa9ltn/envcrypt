"""Watch .env files for changes and automatically re-lock them."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when a watch operation fails."""


def get_mtime(path: Path) -> Optional[float]:
    """Return the modification time of a file, or None if it does not exist."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return None


def watch_env_file(
    env_path: Path,
    on_change: Callable[[Path], None],
    poll_interval: float = 1.0,
    stop_after: Optional[int] = None,
) -> int:
    """Poll *env_path* and call *on_change* whenever the file is modified.

    Parameters
    ----------
    env_path:
        Path to the ``.env`` file to watch.
    on_change:
        Callback invoked with *env_path* each time a change is detected.
    poll_interval:
        Seconds between each poll (default: 1.0).
    stop_after:
        If given, stop after this many change events (useful for testing).

    Returns
    -------
    int
        Number of change events detected before stopping.
    """
    if not env_path.exists():
        raise WatchError(f"env file not found: {env_path}")

    last_mtime = get_mtime(env_path)
    changes_detected = 0

    try:
        while True:
            time.sleep(poll_interval)
            current_mtime = get_mtime(env_path)

            if current_mtime is None:
                # File was deleted; reset baseline when it reappears
                last_mtime = None
                continue

            if current_mtime != last_mtime:
                last_mtime = current_mtime
                changes_detected += 1
                on_change(env_path)

                if stop_after is not None and changes_detected >= stop_after:
                    break
    except KeyboardInterrupt:
        pass

    return changes_detected
