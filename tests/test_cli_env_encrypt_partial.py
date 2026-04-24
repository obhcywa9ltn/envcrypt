"""Tests for envcrypt.cli_env_encrypt_partial."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_env_encrypt_partial import partial_group
from envcrypt.env_encrypt_partial import PartialEncryptError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_PASS=secret\nDEBUG=true\n")
    return p


# ---------------------------------------------------------------------------
# cmd_partial_encrypt
# ---------------------------------------------------------------------------

def test_encrypt_prints_encrypted_key(runner: CliRunner, env_file: Path) -> None:
    with patch(
        "envcrypt.cli_env_encrypt_partial.encrypt_keys",
        return_value={"DB_PASS": "ENC[abc]"},
    ):
        result = runner.invoke(partial_group, ["encrypt", str(env_file), "-k", "DB_PASS", "-r", "age1abc"])
    assert result.exit_code == 0
    assert "encrypted: DB_PASS" in result.output


def test_encrypt_exits_nonzero_on_error(runner: CliRunner, env_file: Path) -> None:
    with patch(
        "envcrypt.cli_env_encrypt_partial.encrypt_keys",
        side_effect=PartialEncryptError("boom"),
    ):
        result = runner.invoke(partial_group, ["encrypt", str(env_file), "-k", "DB_PASS", "-r", "age1abc"])
    assert result.exit_code != 0
    assert "boom" in result.output


def test_encrypt_loads_recipients_from_file(runner: CliRunner, env_file: Path, tmp_path: Path) -> None:
    rec_file = tmp_path / "recipients.json"
    rec_file.write_text('{"alice": "age1alice"}')
    with patch(
        "envcrypt.cli_env_encrypt_partial.encrypt_keys",
        return_value={"DB_PASS": "ENC[xyz]"},
    ) as mock_enc:
        result = runner.invoke(
            partial_group,
            ["encrypt", str(env_file), "-k", "DB_PASS", "-R", str(rec_file)],
        )
    assert result.exit_code == 0
    call_recipients = mock_enc.call_args[0][2]
    assert "age1alice" in call_recipients


def test_encrypt_multiple_keys(runner: CliRunner, env_file: Path) -> None:
    env_file.write_text("A=1\nB=2\n")
    with patch(
        "envcrypt.cli_env_encrypt_partial.encrypt_keys",
        return_value={"A": "ENC[a]", "B": "ENC[b]"},
    ):
        result = runner.invoke(partial_group, ["encrypt", str(env_file), "-k", "A", "-k", "B", "-r", "age1abc"])
    assert result.exit_code == 0
    assert "encrypted: A" in result.output
    assert "encrypted: B" in result.output


# ---------------------------------------------------------------------------
# cmd_partial_ls
# ---------------------------------------------------------------------------

def test_ls_shows_encrypted_keys(runner: CliRunner, env_file: Path) -> None:
    with patch(
        "envcrypt.cli_env_encrypt_partial.list_encrypted_keys",
        return_value=["DB_PASS"],
    ):
        result = runner.invoke(partial_group, ["ls", str(env_file)])
    assert result.exit_code == 0
    assert "DB_PASS" in result.output


def test_ls_prints_empty_message_when_none(runner: CliRunner, env_file: Path) -> None:
    with patch(
        "envcrypt.cli_env_encrypt_partial.list_encrypted_keys",
        return_value=[],
    ):
        result = runner.invoke(partial_group, ["ls", str(env_file)])
    assert result.exit_code == 0
    assert "no encrypted keys" in result.output


def test_ls_exits_nonzero_on_error(runner: CliRunner, env_file: Path) -> None:
    with patch(
        "envcrypt.cli_env_encrypt_partial.list_encrypted_keys",
        side_effect=PartialEncryptError("missing"),
    ):
        result = runner.invoke(partial_group, ["ls", str(env_file)])
    assert result.exit_code != 0
    assert "missing" in result.output
