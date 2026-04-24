"""Partial encryption: encrypt only selected keys in a .env file."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envcrypt.crypto import encrypt_file, AgeEncryptionError


class PartialEncryptError(Exception):
    """Raised when partial encryption fails."""


def _parse_lines(path: Path) -> List[Tuple[str, Optional[str], str]]:
    """Return list of (key_or_none, value_or_none, raw_line)."""
    result = []
    for raw in path.read_text().splitlines(keepends=True):
        line = raw.rstrip("\n")
        if not line or line.lstrip().startswith("#"):
            result.append((None, None, raw))
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result.append((key.strip(), value, raw))
        else:
            result.append((None, None, raw))
    return result


def encrypt_keys(
    env_path: Path,
    keys: List[str],
    recipients: List[str],
    dest: Optional[Path] = None,
    *,
    marker: str = "ENC[",
) -> Dict[str, str]:
    """Encrypt specific keys in *env_path* and write the result to *dest*.

    Values are replaced with ``ENC[<age-ciphertext>]`` inline.  Returns a
    mapping of key -> encrypted token for the keys that were processed.
    """
    if not env_path.exists():
        raise PartialEncryptError(f"env file not found: {env_path}")
    if not keys:
        raise PartialEncryptError("no keys specified for partial encryption")
    if not recipients:
        raise PartialEncryptError("no recipients provided")

    lines = _parse_lines(env_path)
    key_set = set(keys)
    encrypted: Dict[str, str] = {}
    out_lines: List[str] = []

    for key, value, raw in lines:
        if key is None or key not in key_set or value is None:
            out_lines.append(raw if raw.endswith("\n") else raw + "\n")
            continue
        # Skip already-encrypted values
        if value.startswith(marker):
            out_lines.append(raw if raw.endswith("\n") else raw + "\n")
            encrypted[key] = value
            continue
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".val") as tmp_in:
            tmp_in.write(value.encode())
            tmp_in_path = Path(tmp_in.name)
        tmp_out_path = tmp_in_path.with_suffix(".age")
        try:
            encrypt_file(tmp_in_path, tmp_out_path, recipients)
            token = f"{marker}{tmp_out_path.read_bytes().hex()}]"
        except AgeEncryptionError as exc:
            raise PartialEncryptError(f"encryption failed for key {key!r}: {exc}") from exc
        finally:
            tmp_in_path.unlink(missing_ok=True)
            tmp_out_path.unlink(missing_ok=True)
        encrypted[key] = token
        out_lines.append(f"{key}={token}\n")

    dest = dest or env_path
    dest.write_text("".join(out_lines))
    return encrypted


def list_encrypted_keys(env_path: Path, *, marker: str = "ENC[") -> List[str]:
    """Return keys whose values are already partially encrypted."""
    if not env_path.exists():
        raise PartialEncryptError(f"env file not found: {env_path}")
    result = []
    for key, value, _ in _parse_lines(env_path):
        if key and value and value.startswith(marker):
            result.append(key)
    return result
