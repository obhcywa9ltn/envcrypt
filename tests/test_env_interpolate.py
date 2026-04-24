"""Tests for envcrypt.env_interpolate."""
from __future__ import annotations

import pytest
from pathlib import Path

from envcrypt.env_interpolate import (
    InterpolateError,
    interpolate_value,
    interpolate_env_file,
    list_references,
)


# ---------------------------------------------------------------------------
# interpolate_value
# ---------------------------------------------------------------------------

def test_interpolate_value_no_refs():
    assert interpolate_value("hello", {}) == "hello"


def test_interpolate_value_braced():
    assert interpolate_value("${FOO}", {"FOO": "bar"}) == "bar"


def test_interpolate_value_unbraced():
    assert interpolate_value("$FOO", {"FOO": "baz"}) == "baz"


def test_interpolate_value_mixed():
    result = interpolate_value("${A}-$B", {"A": "x", "B": "y"})
    assert result == "x-y"


def test_interpolate_value_raises_on_undefined():
    with pytest.raises(InterpolateError, match="Undefined variable"):
        interpolate_value("${MISSING}", {})


# ---------------------------------------------------------------------------
# interpolate_env_file
# ---------------------------------------------------------------------------

def test_raises_when_src_missing(tmp_path):
    with pytest.raises(InterpolateError, match="not found"):
        interpolate_env_file(tmp_path / "nonexistent.env")


def test_resolves_self_references(tmp_path):
    src = tmp_path / ".env"
    src.write_text("BASE=hello\nGREET=${BASE}_world\n")
    result = interpolate_env_file(src, tmp_path / "out.env")
    assert result["GREET"] == "hello_world"


def test_extra_context_is_used(tmp_path):
    src = tmp_path / ".env"
    src.write_text("MSG=${PREFIX}_suffix\n")
    result = interpolate_env_file(src, tmp_path / "out.env", extra_context={"PREFIX": "hi"})
    assert result["MSG"] == "hi_suffix"


def test_writes_output_file(tmp_path):
    src = tmp_path / ".env"
    dest = tmp_path / "resolved.env"
    src.write_text("A=1\nB=${A}2\n")
    interpolate_env_file(src, dest)
    content = dest.read_text()
    assert "B=12" in content


def test_default_dest_uses_interpolated_suffix(tmp_path):
    src = tmp_path / ".env"
    src.write_text("X=1\n")
    interpolate_env_file(src)
    default_dest = src.with_suffix(".interpolated.env")
    assert default_dest.exists()


def test_raises_on_undefined_in_file(tmp_path):
    src = tmp_path / ".env"
    src.write_text("A=${NOPE}\n")
    with pytest.raises(InterpolateError, match="NOPE"):
        interpolate_env_file(src, tmp_path / "out.env")


# ---------------------------------------------------------------------------
# list_references
# ---------------------------------------------------------------------------

def test_list_references_raises_when_missing(tmp_path):
    with pytest.raises(InterpolateError, match="not found"):
        list_references(tmp_path / "missing.env")


def test_list_references_returns_empty_for_plain_values(tmp_path):
    src = tmp_path / ".env"
    src.write_text("A=plain\nB=also_plain\n")
    refs = list_references(src)
    assert refs == {"A": [], "B": []}


def test_list_references_detects_braced(tmp_path):
    src = tmp_path / ".env"
    src.write_text("A=1\nB=${A}\n")
    refs = list_references(src)
    assert refs["B"] == ["A"]


def test_list_references_detects_multiple(tmp_path):
    src = tmp_path / ".env"
    src.write_text("C=$X-${Y}\n")
    refs = list_references(src)
    assert set(refs["C"]) == {"X", "Y"}
