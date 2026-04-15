"""Tests for envcrypt.cli."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli import cli
from envcrypt.keys import KeyError as EnvKeyError
from envcrypt.recipients import RecipientsError
from envcrypt.vault import VaultError


@pytest.fixture()
def runner():
    return CliRunner()


class TestCmdInit:
    def test_prints_keys_on_success(self, runner):
        with patch("envcrypt.cli.generate_keypair", return_value=("age1pub", "AGE-SECRET-KEY-1priv")):
            result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "age1pub" in result.output
        assert "AGE-SECRET-KEY-1priv" in result.output

    def test_exits_nonzero_on_error(self, runner):
        with patch("envcrypt.cli.generate_keypair", side_effect=EnvKeyError("age missing")):
            result = runner.invoke(cli, ["init"])
        assert result.exit_code == 1
        assert "age missing" in result.output


class TestCmdAdd:
    def test_adds_recipient_successfully(self, runner):
        with patch("envcrypt.cli.add_recipient") as mock_add:
            result = runner.invoke(cli, ["add", "alice", "age1abc", "--recipients", "r.json"])
        assert result.exit_code == 0
        assert "alice" in result.output
        mock_add.assert_called_once_with("r.json", "alice", "age1abc")

    def test_exits_nonzero_on_error(self, runner):
        with patch("envcrypt.cli.add_recipient", side_effect=RecipientsError("bad file")):
            result = runner.invoke(cli, ["add", "alice", "age1abc"])
        assert result.exit_code == 1
        assert "bad file" in result.output


class TestCmdList:
    def test_lists_recipients(self, runner):
        with patch("envcrypt.cli.load_recipients", return_value={"alice": "age1abc", "bob": "age1xyz"}):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "alice" in result.output
        assert "bob" in result.output

    def test_shows_empty_message(self, runner):
        with patch("envcrypt.cli.load_recipients", return_value={}):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No recipients" in result.output

    def test_exits_nonzero_on_error(self, runner):
        with patch("envcrypt.cli.load_recipients", side_effect=RecipientsError("oops")):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 1


class TestCmdLock:
    def test_prints_output_path(self, runner, tmp_path):
        out = tmp_path / ".envcrypt" / ".env.age"
        with patch("envcrypt.cli.lock", return_value=out):
            result = runner.invoke(cli, ["lock", ".env"])
        assert result.exit_code == 0
        assert str(out) in result.output

    def test_exits_nonzero_on_vault_error(self, runner):
        with patch("envcrypt.cli.lock", side_effect=VaultError("no recipients")):
            result = runner.invoke(cli, ["lock", ".env"])
        assert result.exit_code == 1
        assert "no recipients" in result.output


class TestCmdUnlock:
    def test_prints_output_path(self, runner, tmp_path):
        out = tmp_path / ".env"
        with patch("envcrypt.cli.unlock", return_value=out), \
             patch("envcrypt.cli.get_key_file", return_value=tmp_path / "key.txt"):
            result = runner.invoke(cli, ["unlock", ".envcrypt/.env.age"])
        assert result.exit_code == 0
        assert str(out) in result.output

    def test_exits_nonzero_on_vault_error(self, runner, tmp_path):
        with patch("envcrypt.cli.unlock", side_effect=VaultError("bad key")), \
             patch("envcrypt.cli.get_key_file", return_value=tmp_path / "key.txt"):
            result = runner.invoke(cli, ["unlock", ".envcrypt/.env.age"])
        assert result.exit_code == 1
        assert "bad key" in result.output

    def test_exits_nonzero_when_no_identity_found(self, runner):
        with patch("envcrypt.cli.get_key_file", side_effect=EnvKeyError("key not found")):
            result = runner.invoke(cli, ["unlock", ".envcrypt/.env.age"])
        assert result.exit_code == 1
        assert "key not found" in result.output
