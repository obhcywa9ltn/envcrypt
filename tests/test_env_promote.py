"""Tests for envcrypt.env_promote."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.env_promote import PromoteError, list_promotable_keys, promote_keys
from envcrypt.cli_env_promote import promote_group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------------------
# promote_keys
# ---------------------------------------------------------------------------

def test_raises_when_src_missing(tmp_path: Path) -> None:
    with pytest.raises(PromoteError, match="Source env file not found"):
        promote_keys(tmp_path / "missing.env", tmp_path / "dest.env")


def test_raises_when_key_missing_in_src(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    _write(src, "FOO=bar\n")
    with pytest.raises(PromoteError, match="Key 'NOPE' not found in source"):
        promote_keys(src, tmp_path / "dest.env", keys=["NOPE"])


def test_raises_on_conflict_without_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "FOO=new\n")
    _write(dest, "FOO=old\n")
    with pytest.raises(PromoteError, match="already exists"):
        promote_keys(src, dest, keys=["FOO"], overwrite=False)


def test_promotes_all_keys_by_default(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "A=1\nB=2\n")
    promoted = promote_keys(src, dest)
    assert promoted == {"A": "1", "B": "2"}
    assert "A=1" in dest.read_text()
    assert "B=2" in dest.read_text()


def test_promotes_selected_keys_only(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "A=1\nB=2\nC=3\n")
    promoted = promote_keys(src, dest, keys=["A", "C"])
    assert set(promoted.keys()) == {"A", "C"}
    dest_text = dest.read_text()
    assert "B=" not in dest_text


def test_overwrite_replaces_existing_key(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "FOO=new\n")
    _write(dest, "FOO=old\nBAR=keep\n")
    promote_keys(src, dest, keys=["FOO"], overwrite=True)
    dest_text = dest.read_text()
    assert "FOO=new" in dest_text
    assert "BAR=keep" in dest_text


def test_creates_dest_file_when_absent(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "subdir" / "dest.env"
    _write(src, "KEY=val\n")
    promote_keys(src, dest)
    assert dest.exists()
    assert "KEY=val" in dest.read_text()


# ---------------------------------------------------------------------------
# list_promotable_keys
# ---------------------------------------------------------------------------

def test_list_promotable_raises_when_src_missing(tmp_path: Path) -> None:
    with pytest.raises(PromoteError):
        list_promotable_keys(tmp_path / "missing.env", tmp_path / "dest.env")


def test_list_promotable_categorises_correctly(tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "A=1\nB=2\nC=3\n")
    _write(dest, "B=old\n")
    result = list_promotable_keys(src, dest)
    assert set(result["new"]) == {"A", "C"}
    assert result["existing"] == ["B"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_promote_run_success(runner: CliRunner, tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "X=1\n")
    result = runner.invoke(promote_group, ["run", str(src), str(dest)])
    assert result.exit_code == 0
    assert "promoted: X" in result.output


def test_cli_promote_run_exits_nonzero_on_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(promote_group, ["run", str(tmp_path / "no.env"), str(tmp_path / "d.env")])
    assert result.exit_code != 0


def test_cli_promote_diff_shows_categories(runner: CliRunner, tmp_path: Path) -> None:
    src = tmp_path / "src.env"
    dest = tmp_path / "dest.env"
    _write(src, "NEW=1\nOLD=2\n")
    _write(dest, "OLD=x\n")
    result = runner.invoke(promote_group, ["diff", str(src), str(dest)])
    assert result.exit_code == 0
    assert "NEW" in result.output
    assert "OLD" in result.output
