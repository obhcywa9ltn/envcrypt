"""Git hook management for envcrypt — install/remove pre-commit hooks that
auto-lock .env files before commits."""

from __future__ import annotations

import os
import stat
from pathlib import Path

HOOK_MARKER = "# envcrypt-hook"
HOOK_SCRIPT = """\
#!/bin/sh
# envcrypt-hook
# Auto-lock .env files tracked by envcrypt before committing.
envcrypt lock 2>&1
if [ $? -ne 0 ]; then
    echo "envcrypt: failed to lock .env files — commit aborted." >&2
    exit 1
fi
"""


class HookError(Exception):
    """Raised when a git hook operation fails."""


def get_hooks_dir(base_dir: str | None = None) -> Path:
    """Return the .git/hooks directory relative to *base_dir* (or cwd)."""
    root = Path(base_dir) if base_dir else Path.cwd()
    return root / ".git" / "hooks"


def get_hook_path(base_dir: str | None = None) -> Path:
    """Return the path to the pre-commit hook file."""
    return get_hooks_dir(base_dir) / "pre-commit"


def is_hook_installed(base_dir: str | None = None) -> bool:
    """Return True if the envcrypt pre-commit hook is present."""
    hook = get_hook_path(base_dir)
    if not hook.exists():
        return False
    return HOOK_MARKER in hook.read_text()


def install_hook(base_dir: str | None = None) -> Path:
    """Install the envcrypt pre-commit hook.

    If a pre-commit hook already exists and does *not* contain the envcrypt
    marker, the new script is appended rather than replacing the file.

    Returns the path to the hook file.
    Raises HookError if the .git/hooks directory does not exist.
    """
    hooks_dir = get_hooks_dir(base_dir)
    if not hooks_dir.exists():
        raise HookError(
            f"hooks directory not found: {hooks_dir}. "
            "Is this a git repository?"
        )

    hook = get_hook_path(base_dir)

    if hook.exists():
        content = hook.read_text()
        if HOOK_MARKER in content:
            return hook  # already installed — idempotent
        # Append to existing hook
        hook.write_text(content.rstrip("\n") + "\n" + HOOK_SCRIPT)
    else:
        hook.write_text("#!/bin/sh\n" + HOOK_SCRIPT)

    # Ensure the hook is executable
    current = hook.stat().st_mode
    hook.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hook


def remove_hook(base_dir: str | None = None) -> bool:
    """Remove the envcrypt block from the pre-commit hook.

    Returns True if the hook was modified/removed, False if it was not present.
    """
    hook = get_hook_path(base_dir)
    if not hook.exists():
        return False

    content = hook.read_text()
    if HOOK_MARKER not in content:
        return False

    lines = content.splitlines(keepends=True)
    filtered = [line for line in lines if HOOK_MARKER not in line]
    # Remove lines that are part of the envcrypt block
    new_content = "".join(
        line for line in filtered
        if not any(cmd in line for cmd in ["envcrypt lock", "envcrypt: failed"])
    )

    if new_content.strip() in ("", "#!/bin/sh"):
        hook.unlink()
    else:
        hook.write_text(new_content)
    return True
