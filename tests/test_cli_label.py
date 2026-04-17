"""Tests for envcrypt.cli_label."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envcrypt.cli_label import label_group
from envcrypt.label import LabelError


@pytest.fixture
def runner():
    return CliRunner()


def test_add_prints_success(runner):
    with patch("envcrypt.cli_label.add_label", return_value={"prod": [".env.prod"]}) as m:
        result = runner.invoke(label_group, ["add", "prod", ".env.prod"])
    assert result.exit_code == 0
    assert "prod" in result.output


def test_add_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_label.add_label", side_effect=LabelError("already exists")):
        result = runner.invoke(label_group, ["add", "prod", ".env.prod"])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_remove_prints_success(runner):
    with patch("envcrypt.cli_label.remove_label", return_value={}):
        result = runner.invoke(label_group, ["remove", "prod"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_label.remove_label", side_effect=LabelError("not found")):
        result = runner.invoke(label_group, ["remove", "ghost"])
    assert result.exit_code != 0


def test_list_prints_labels(runner):
    with patch("envcrypt.cli_label.load_labels", return_value={"dev": [".env"], "prod": [".env.prod"]}):
        result = runner.invoke(label_group, ["list"])
    assert result.exit_code == 0
    assert "dev" in result.output
    assert "prod" in result.output


def test_list_prints_empty_message(runner):
    with patch("envcrypt.cli_label.load_labels", return_value={}):
        result = runner.invoke(label_group, ["list"])
    assert result.exit_code == 0
    assert "No labels" in result.output


def test_show_prints_files(runner):
    with patch("envcrypt.cli_label.get_label", return_value=[".env.prod", ".env.secrets"]):
        result = runner.invoke(label_group, ["show", "prod"])
    assert result.exit_code == 0
    assert ".env.prod" in result.output


def test_show_exits_nonzero_on_error(runner):
    with patch("envcrypt.cli_label.get_label", side_effect=LabelError("not found")):
        result = runner.invoke(label_group, ["show", "nope"])
    assert result.exit_code != 0
