import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envcrypt.cli_access import access_group
from envcrypt.access import AccessError


@pytest.fixture
def runner():
    return CliRunner()


def test_grant_prints_success(runner):
    with patch("envcrypt.cli_access.grant_access", return_value={"prod": ["age1abc"]}):
        result = runner.invoke(access_group, ["grant", "prod", "age1abc"])
    assert result.exit_code == 0
    assert "Granted" in result.output


def test_grant_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_access.grant_access", side_effect=AccessError("fail")):
        result = runner.invoke(access_group, ["grant", "prod", "age1abc"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_revoke_prints_success(runner):
    with patch("envcrypt.cli_access.revoke_access", return_value={"prod": []}):
        result = runner.invoke(access_group, ["revoke", "prod", "age1abc"])
    assert result.exit_code == 0
    assert "Revoked" in result.output


def test_revoke_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_access.revoke_access", side_effect=AccessError("not found")):
        result = runner.invoke(access_group, ["revoke", "prod", "age1abc"])
    assert result.exit_code != 0


def test_list_shows_rules(runner):
    with patch("envcrypt.cli_access.load_access", return_value={"prod": ["age1abc"]}):
        result = runner.invoke(access_group, ["list"])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "age1abc" in result.output


def test_list_shows_empty_message(runner):
    with patch("envcrypt.cli_access.load_access", return_value={}):
        result = runner.invoke(access_group, ["list"])
    assert result.exit_code == 0
    assert "No access rules" in result.output


def test_check_allowed(runner):
    with patch("envcrypt.cli_access.is_allowed", return_value=True):
        result = runner.invoke(access_group, ["check", "prod", "age1abc"])
    assert result.exit_code == 0
    assert "allowed" in result.output


def test_check_denied_exits_nonzero(runner):
    with patch("envcrypt.cli_access.is_allowed", return_value=False):
        result = runner.invoke(access_group, ["check", "prod", "age1other"])
    assert result.exit_code != 0
    assert "NOT allowed" in result.output
