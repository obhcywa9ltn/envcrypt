"""Template support for .env files — generate .env.example from encrypted vault."""

from __future__ import annotations

import re
from pathlib import Path

from envcrypt.vault import get_vault_dir, get_encrypted_path, unlock, VaultError


class TemplateError(Exception):
    """Raised when template generation or application fails."""


def generate_template(env_file: Path, dest: Path | None = None) -> Path:
    """Parse *env_file* and write a .env.example with values redacted.

    Args:
        env_file: Path to the plain-text .env source file.
        dest: Destination path; defaults to *env_file* with `.example` suffix.

    Returns:
        The path to the written template file.
    """
    if not env_file.exists():
        raise TemplateError(f"env file not found: {env_file}")

    if dest is None:
        dest = env_file.with_suffix(".example")

    lines: list[str] = []
    for raw in env_file.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            lines.append(raw)
        elif "=" in stripped:
            key, _ = stripped.split("=", 1)
            lines.append(f"{key}=")
        else:
            lines.append(raw)

    dest.write_text("\n".join(lines) + "\n")
    return dest


def apply_template(template_file: Path, values: dict[str, str], dest: Path) -> Path:
    """Fill *template_file* placeholders with *values* and write to *dest*.

    Lines of the form ``KEY=`` (empty value) are filled from *values*.
    Lines already containing a value are left untouched.

    Returns:
        The path to the populated file.
    """
    if not template_file.exists():
        raise TemplateError(f"template file not found: {template_file}")

    lines: list[str] = []
    for raw in template_file.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            lines.append(raw)
        elif "=" in stripped:
            key, value = stripped.split("=", 1)
            if value == "" and key in values:
                lines.append(f"{key}={values[key]}")
            else:
                lines.append(raw)
        else:
            lines.append(raw)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n")
    return dest


def template_from_vault(
    private_key_file: Path,
    base_name: str,
    dest: Path,
    vault_dir: Path | None = None,
) -> Path:
    """Decrypt *base_name* from the vault and write a redacted template to *dest*."""
    vault = get_vault_dir(base_dir=vault_dir)
    encrypted = get_encrypted_path(base_name, vault_dir=vault)
    if not encrypted.exists():
        raise TemplateError(f"no encrypted file found for '{base_name}'")

    try:
        plain_text = unlock(private_key_file, base_name, vault_dir=vault)
    except VaultError as exc:
        raise TemplateError(str(exc)) from exc

    tmp = dest.parent / f".tmp_{base_name}"
    tmp.write_text(plain_text)
    try:
        result = generate_template(tmp, dest=dest)
    finally:
        tmp.unlink(missing_ok=True)
    return result
