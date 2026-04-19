"""Tests for envcrypt.env_mask."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.env_mask import MaskError, mask_value, mask_env_file, show_masked
from envcrypt.cli_env_mask import mask_group


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_hides_leading_chars():
    assert mask_value("abcdefgh", visible=4) == "****efgh"


def test_mask_value_short_value_fully_masked():
    assert mask_value("ab", visible=4) == "**"


def test_mask_value_custom_char():
    assert mask_value("secret", visible=2, char="-") == "----et"


# ---------------------------------------------------------------------------
# mask_env_file
# ---------------------------------------------------------------------------

def test_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(MaskError, match="not found"):
        mask_env_file(tmp_path / "missing.env")


def test_masks_all_keys_by_default(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("FOO=hello\nBAR=world\n")
    masked = mask_env_file(src, dest=tmp_path / "out.env", visible=2)
    assert masked["FOO"] == "***lo"
    assert masked["BAR"] == "***ld"


def test_masks_only_specified_keys(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("FOO=hello\nBAR=world\n")
    dest = tmp_path / "out.env"
    masked = mask_env_file(src, dest=dest, keys=["FOO"], visible=2)
    assert "FOO" in masked
    assert "BAR" not in masked
    content = dest.read_text()
    assert "BAR=world" in content


def test_preserves_comments_and_blanks(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("# comment\n\nFOO=bar\n")
    dest = tmp_path / "out.env"
    mask_env_file(src, dest=dest)
    content = dest.read_text()
    assert "# comment" in content


def test_default_dest_uses_masked_suffix(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("X=123\n")
    mask_env_file(src)
    assert (tmp_path / ".masked").exists()


# ---------------------------------------------------------------------------
# show_masked
# ---------------------------------------------------------------------------

def test_show_masked_raises_when_missing(tmp_path: Path):
    with pytest.raises(MaskError):
        show_masked(tmp_path / "nope.env")


def test_show_masked_returns_dict(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("KEY=supersecret\n")
    result = show_masked(src, visible=4)
    assert result["KEY"] == "*********cret"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_run_prints_success(runner, tmp_path):
    src = tmp_path / ".env"
    src.write_text("TOKEN=abcdefgh\n")
    dest = tmp_path / "out.env"
    result = runner.invoke(mask_group, ["run", str(src), "--dest", str(dest)])
    assert result.exit_code == 0
    assert "Masked" in result.output


def test_cli_run_exits_nonzero_on_error(runner, tmp_path):
    result = runner.invoke(mask_group, ["run", str(tmp_path / "missing.env")])
    assert result.exit_code != 0


def test_cli_show_prints_keys(runner, tmp_path):
    src = tmp_path / ".env"
    src.write_text("SECRET=password123\n")
    result = runner.invoke(mask_group, ["show", str(src), "--visible", "3"])
    assert result.exit_code == 0
    assert "SECRET=" in result.output
