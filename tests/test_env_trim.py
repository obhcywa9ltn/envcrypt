"""Tests for envcrypt.env_trim."""
from __future__ import annotations

from pathlib import Path

import pytest

from envcrypt.env_trim import TrimError, trim_env_file, list_untrimmed_keys


@pytest.fixture()
def env_file(tmp_path: Path):
    """Return a helper that writes a .env file and returns its path."""
    def _make(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _make


def test_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(TrimError, match="not found"):
        trim_env_file(tmp_path / "missing.env")


def test_list_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(TrimError, match="not found"):
        list_untrimmed_keys(tmp_path / "missing.env")


def test_trims_value_with_leading_space(env_file, tmp_path: Path) -> None:
    src = env_file("KEY=  hello\n")
    changed = trim_env_file(src)
    assert changed == {"KEY": "hello"}
    assert src.read_text() == "KEY=hello\n"


def test_trims_value_with_trailing_space(env_file) -> None:
    src = env_file("KEY=world   \n")
    changed = trim_env_file(src)
    assert changed == {"KEY": "world"}


def test_no_change_when_already_clean(env_file) -> None:
    src = env_file("KEY=value\n")
    changed = trim_env_file(src)
    assert changed == {}


def test_writes_to_dest(env_file, tmp_path: Path) -> None:
    src = env_file("A= 1 \nB=2\n")
    dest = tmp_path / "out.env"
    trim_env_file(src, dest)
    assert dest.read_text() == "A=1\nB=2\n"
    # src unchanged
    assert src.read_text() == "A= 1 \nB=2\n"


def test_limits_to_specified_keys(env_file) -> None:
    src = env_file("A= 1 \nB= 2 \n")
    changed = trim_env_file(src, keys=["A"])
    assert changed == {"A": "1"}
    assert "B= 2 " in src.read_text()


def test_preserves_comments_and_blanks(env_file) -> None:
    content = "# comment\n\nKEY= val \n"
    src = env_file(content)
    trim_env_file(src)
    result = src.read_text()
    assert "# comment" in result
    assert "\n\n" in result


def test_list_untrimmed_keys_returns_correct(env_file) -> None:
    src = env_file("A= 1\nB=clean\nC=trailing  \n")
    keys = list_untrimmed_keys(src)
    assert "A" in keys
    assert "C" in keys
    assert "B" not in keys


def test_list_untrimmed_keys_empty_for_clean_file(env_file) -> None:
    src = env_file("X=1\nY=two\n")
    assert list_untrimmed_keys(src) == []
