"""Light integration tests — run generate then apply end-to-end without mocks."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envcrypt.cli_template import template_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def test_generate_then_apply_roundtrip(runner: CliRunner, tmp_path: Path):
    """generate strips values; apply restores them via --set."""
    env = tmp_path / ".env"
    env.write_text("API_KEY=secret123\nDEBUG=true\n")

    # Generate template
    tmpl = tmp_path / ".env.example"
    result = runner.invoke(
        template_group, ["generate", str(env), "--dest", str(tmpl)]
    )
    assert result.exit_code == 0, result.output
    assert tmpl.exists()
    template_content = tmpl.read_text()
    assert "secret123" not in template_content
    assert "API_KEY=" in template_content

    # Apply values back
    dest = tmp_path / ".env.filled"
    result = runner.invoke(
        template_group,
        [
            "apply",
            str(tmpl),
            str(dest),
            "--set",
            "API_KEY=secret123",
            "--set",
            "DEBUG=true",
        ],
    )
    assert result.exit_code == 0, result.output
    assert dest.exists()
    filled = dest.read_text()
    assert "API_KEY=secret123" in filled
    assert "DEBUG=true" in filled


def test_generate_preserves_comments(runner: CliRunner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("# App settings\n\nPORT=8080\n")
    tmpl = tmp_path / ".env.example"

    result = runner.invoke(
        template_group, ["generate", str(env), "--dest", str(tmpl)]
    )
    assert result.exit_code == 0
    content = tmpl.read_text()
    assert "# App settings" in content
    assert "8080" not in content
    assert "PORT=" in content
