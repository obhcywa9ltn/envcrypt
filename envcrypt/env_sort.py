"""Sort .env file keys alphabetically or by custom order."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional


class SortError(Exception):
    pass


def _parse_lines(path: Path) -> List[str]:
    try:
        return path.read_text().splitlines()
    except OSError as exc:
        raise SortError(f"Cannot read file: {exc}") from exc


def sort_env_file(
    src: Path,
    dest: Optional[Path] = None,
    reverse: bool = False,
    group_comments: bool = True,
) -> Path:
    """Sort key=value lines alphabetically; preserve leading comment blocks."""
    if not src.exists():
        raise SortError(f"File not found: {src}")

    lines = _parse_lines(src)
    header: List[str] = []
    body: List[str] = []

    # Collect leading comment / blank header
    idx = 0
    if group_comments:
        while idx < len(lines) and (lines[idx].startswith("#") or lines[idx].strip() == ""):
            header.append(lines[idx])
            idx += 1

    body = lines[idx:]

    kv_lines = [l for l in body if "=" in l and not l.startswith("#")]
    other_lines = [l for l in body if "=" not in l or l.startswith("#")]

    kv_lines.sort(key=lambda l: l.split("=", 1)[0].strip().lower(), reverse=reverse)

    sorted_lines = header + other_lines + kv_lines

    out = dest if dest is not None else src
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(sorted_lines) + "\n")
    return out


def sorted_keys(src: Path) -> List[str]:
    """Return sorted list of keys present in the env file."""
    if not src.exists():
        raise SortError(f"File not found: {src}")
    keys = []
    for line in _parse_lines(src):
        if "=" in line and not line.startswith("#"):
            keys.append(line.split("=", 1)[0].strip())
    return sorted(keys)
