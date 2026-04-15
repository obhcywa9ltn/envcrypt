"""Tests for envcrypt.template."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envcrypt.template import (
    TemplateError,
    generate_template,
    apply_template,
    template_from_vault,
)


# ---------------------------------------------------------------------------
# generate_template
# ---------------------------------------------------------------------------

class TestGenerateTemplate:
    def test_raises_when_env_file_missing(self, tmp_path: Path):
        with pytest.raises(TemplateError, match="env file not found"):
            generate_template(tmp_path / "missing.env")

    def test_redacts_values(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("FOO=bar\nBAZ=secret\n")
        out = generate_template(env)
        content = out.read_text()
        assert "FOO=" in content
        assert "bar" not in content
        assert "BAZ=" in content
        assert "secret" not in content

    def test_preserves_comments_and_blanks(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("# comment\n\nFOO=bar\n")
        out = generate_template(env)
        content = out.read_text()
        assert "# comment" in content

    def test_default_dest_uses_example_suffix(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY=value\n")
        out = generate_template(env)
        assert out.name == ".example"

    def test_custom_dest(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY=value\n")
        dest = tmp_path / "custom.example"
        out = generate_template(env, dest=dest)
        assert out == dest
        assert dest.exists()


# ---------------------------------------------------------------------------
# apply_template
# ---------------------------------------------------------------------------

class TestApplyTemplate:
    def test_raises_when_template_missing(self, tmp_path: Path):
        with pytest.raises(TemplateError, match="template file not found"):
            apply_template(tmp_path / "missing.example", {}, tmp_path / "out.env")

    def test_fills_empty_values(self, tmp_path: Path):
        tmpl = tmp_path / ".env.example"
        tmpl.write_text("FOO=\nBAR=\n")
        dest = tmp_path / ".env"
        apply_template(tmpl, {"FOO": "hello", "BAR": "world"}, dest)
        content = dest.read_text()
        assert "FOO=hello" in content
        assert "BAR=world" in content

    def test_leaves_existing_values_untouched(self, tmp_path: Path):
        tmpl = tmp_path / ".env.example"
        tmpl.write_text("FOO=already_set\n")
        dest = tmp_path / ".env"
        apply_template(tmpl, {"FOO": "overridden"}, dest)
        assert "already_set" in dest.read_text()

    def test_creates_dest_directory(self, tmp_path: Path):
        tmpl = tmp_path / ".env.example"
        tmpl.write_text("KEY=\n")
        dest = tmp_path / "sub" / "dir" / ".env"
        apply_template(tmpl, {"KEY": "val"}, dest)
        assert dest.exists()


# ---------------------------------------------------------------------------
# template_from_vault
# ---------------------------------------------------------------------------

class TestTemplateFromVault:
    def test_raises_when_encrypted_file_missing(self, tmp_path: Path):
        vault = tmp_path / ".envcrypt"
        vault.mkdir()
        with pytest.raises(TemplateError, match="no encrypted file found"):
            template_from_vault(
                private_key_file=tmp_path / "key.txt",
                base_name="production",
                dest=tmp_path / "out.example",
                vault_dir=tmp_path,
            )

    def test_generates_template_from_decrypted_content(self, tmp_path: Path):
        vault = tmp_path / ".envcrypt"
        vault.mkdir()
        (vault / "production.env.age").write_text("dummy")

        plain = "SECRET=supersecret\nDEBUG=true\n"

        with patch("envcrypt.template.unlock", return_value=plain) as mock_unlock:
            dest = tmp_path / "production.env.example"
            result = template_from_vault(
                private_key_file=tmp_path / "key.txt",
                base_name="production",
                dest=dest,
                vault_dir=tmp_path,
            )

        assert result == dest
        content = dest.read_text()
        assert "SECRET=" in content
        assert "supersecret" not in content
        mock_unlock.assert_called_once()
