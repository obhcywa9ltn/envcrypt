"""Search for keys across env files in the vault."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envcrypt.vault import get_vault_dir, get_encrypted_path, unlock
from envcrypt.keys import get_key_file


class SearchError(Exception):
    pass


@dataclass
class SearchMatch:
    env_name: str
    key: str
    value: str


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0


def search_vault(
    pattern: str,
    base_dir: Optional[Path] = None,
    key_file: Optional[Path] = None,
    search_values: bool = False,
) -> SearchResult:
    """Search for keys (and optionally values) matching *pattern* across all
    encrypted env files in the vault."""
    vault_dir = get_vault_dir(base_dir=base_dir)
    if not vault_dir.exists():
        raise SearchError(f"Vault directory not found: {vault_dir}")

    if key_file is None:
        key_file = get_key_file()

    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise SearchError(f"Invalid pattern '{pattern}': {exc}") from exc

    result = SearchResult()

    for encrypted_path in sorted(vault_dir.glob("*.age")):
        env_name = encrypted_path.stem
        try:
            plaintext = unlock(env_name, base_dir=base_dir, key_file=key_file)
        except Exception:
            continue

        for line in plaintext.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            target = key if not search_values else f"{key}={value}"
            if rx.search(target):
                result.matches.append(SearchMatch(env_name=env_name, key=key, value=value))

    return result
