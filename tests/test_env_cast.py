"""Tests for envcrypt.env_cast."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.env_cast import CastError, cast_env_file, cast_value, infer_types
from envcrypt.cli_env_cast import cast_group


# ---------------------------------------------------------------------------
# cast_value
# ---------------------------------------------------------------------------

def test_cast_str_returns_string():
    assert cast_value("hello", "str") == "hello"


def test_cast_int_valid():
    assert cast_value("42", "int") == 42


def test_cast_int_invalid_raises():
    with pytest.raises(CastError, match="Cannot cast"):
        cast_value("abc", "int")


def test_cast_float_valid():
    assert cast_value("3.14", "float") == pytest.approx(3.14)


def test_cast_float_invalid_raises():
    with pytest.raises(CastError):
        cast_value("nope", "float")


@pytest.mark.parametrize("raw", ["true", "True", "1", "yes", "on"])
def test_cast_bool_truthy(raw: str):
    assert cast_value(raw, "bool") is True


@pytest.mark.parametrize("raw", ["false", "False", "0", "no", "off"])
def test_cast_bool_falsy(raw: str):
    assert cast_value(raw, "bool") is False


def test_cast_bool_invalid_raises():
    with pytest.raises(CastError):
        cast_value("maybe", "bool")


def test_cast_unknown_type_raises():
    with pytest.raises(CastError, match="Unknown target type"):
        cast_value("x", "list")


# ---------------------------------------------------------------------------
# cast_env_file
# ---------------------------------------------------------------------------

def test_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(CastError, match="not found"):
        cast_env_file(tmp_path / "missing.env", {})


def test_casts_according_to_schema(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("PORT=8080\nDEBUG=true\nRATE=1.5\nNAME=app\n")
    result = cast_env_file(env, {"PORT": "int", "DEBUG": "bool", "RATE": "float"})
    assert result["PORT"] == 8080
    assert result["DEBUG"] is True
    assert result["RATE"] == pytest.approx(1.5)
    assert result["NAME"] == "app"


def test_ignores_comments_and_blanks(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("# comment\n\nKEY=value\n")
    result = cast_env_file(env, {})
    assert result == {"KEY": "value"}


# ---------------------------------------------------------------------------
# infer_types
# ---------------------------------------------------------------------------

def test_infer_raises_when_file_missing(tmp_path: Path):
    with pytest.raises(CastError):
        infer_types(tmp_path / "missing.env")


def test_infer_detects_types(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("PORT=8080\nDEBUG=true\nRATE=1.5\nNAME=app\n")
    schema = infer_types(env)
    assert schema["PORT"] == "int"
    assert schema["DEBUG"] == "bool"
    assert schema["RATE"] == "float"
    assert schema["NAME"] == "str"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cmd_cast_run_prints_json(runner: CliRunner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("PORT=9000\n")
    schema = json.dumps({"PORT": "int"})
    result = runner.invoke(cast_group, ["run", str(env), "--schema", schema])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["PORT"] == 9000


def test_cmd_cast_run_invalid_schema_exits_nonzero(runner: CliRunner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("KEY=val\n")
    result = runner.invoke(cast_group, ["run", str(env), "--schema", "not-json"])
    assert result.exit_code != 0


def test_cmd_cast_value_int(runner: CliRunner):
    result = runner.invoke(cast_group, ["value", "7", "int"])
    assert result.exit_code == 0
    assert "7" in result.output


def test_cmd_cast_infer_prints_schema(runner: CliRunner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("WORKERS=4\nENABLED=false\n")
    result = runner.invoke(cast_group, ["infer", str(env)])
    assert result.exit_code == 0
    schema = json.loads(result.output)
    assert schema["WORKERS"] == "int"
    assert schema["ENABLED"] == "bool"
