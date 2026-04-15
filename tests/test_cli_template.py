"""Tests for envcrypt.cli_template."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_template import template_group
from envcrypt.template import TemplateError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


# ---------------------------------------------------------------------------
# cmd_template_generate
# ---------------------------------------------------------------------------

class TestCmdTemplateGenerate:
    def test_prints_success_message(self, runner: CliRunner, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY=value\n")
        dest = tmp_path / ".env.example"

        with patch(
            "envcrypt.cli_template.generate_template", return_value=dest
        ) as mock_gen:
            result = runner.invoke(
                template_group, ["generate", str(env), "--dest", str(dest)]
            )

        assert result.exit_code == 0
        assert str(dest) in result.output
        mock_gen.assert_called_once_with(env, dest=dest)

    def test_exits_nonzero_on_error(self, runner: CliRunner, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY=val\n")

        with patch(
            "envcrypt.cli_template.generate_template",
            side_effect=TemplateError("boom"),
        ):
            result = runner.invoke(template_group, ["generate", str(env)])

        assert result.exit_code == 1
        assert "boom" in result.stderr


# ---------------------------------------------------------------------------
# cmd_template_apply
# ---------------------------------------------------------------------------

class TestCmdTemplateApply:
    def test_prints_success_message(self, runner: CliRunner, tmp_path: Path):
        tmpl = tmp_path / ".env.example"
        tmpl.write_text("KEY=\n")
        dest = tmp_path / ".env"

        with patch(
            "envcrypt.cli_template.apply_template", return_value=dest
        ) as mock_apply:
            result = runner.invoke(
                template_group,
                ["apply", str(tmpl), str(dest), "--set", "KEY=hello"],
            )

        assert result.exit_code == 0
        assert str(dest) in result.output
        mock_apply.assert_called_once_with(tmpl, {"KEY": "hello"}, dest)

    def test_exits_nonzero_on_invalid_pair(self, runner: CliRunner, tmp_path: Path):
        tmpl = tmp_path / ".env.example"
        tmpl.write_text("KEY=\n")
        dest = tmp_path / ".env"

        result = runner.invoke(
            template_group,
            ["apply", str(tmpl), str(dest), "--set", "BADPAIR"],
        )

        assert result.exit_code == 1
        assert "BADPAIR" in result.stderr

    def test_exits_nonzero_on_error(self, runner: CliRunner, tmp_path: Path):
        tmpl = tmp_path / ".env.example"
        tmpl.write_text("KEY=\n")
        dest = tmp_path / ".env"

        with patch(
            "envcrypt.cli_template.apply_template",
            side_effect=TemplateError("apply failed"),
        ):
            result = runner.invoke(
                template_group, ["apply", str(tmpl), str(dest)]
            )

        assert result.exit_code == 1
        assert "apply failed" in result.stderr
