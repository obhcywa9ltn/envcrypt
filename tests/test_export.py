"""Tests for envcrypt.export."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envcrypt.export import ExportError, export_env, import_env, list_exports


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vault(tmp_path: Path, *names: str) -> Path:
    vault = tmp_path / ".envcrypt" / "vault"
    vault.mkdir(parents=True)
    for name in names:
        (vault / f"{name}.age").write_bytes(b"encrypted")
    return vault


# ---------------------------------------------------------------------------
# export_env
# ---------------------------------------------------------------------------


class TestExportEnv:
    def test_raises_when_encrypted_file_missing(self, tmp_path):
        with pytest.raises(ExportError, match="No encrypted file found"):
            export_env("missing", tmp_path / "out", base_dir=tmp_path)

    def test_copies_file_to_dest(self, tmp_path):
        _make_vault(tmp_path, "staging")
        out_dir = tmp_path / "exports"

        with patch("envcrypt.export.append_audit_entry"):
            result = export_env("staging", out_dir, base_dir=tmp_path)

        assert result.exists()
        assert result.name == "staging.age"
        assert result.parent == out_dir

    def test_creates_dest_directory_if_missing(self, tmp_path):
        _make_vault(tmp_path, "prod")
        out_dir = tmp_path / "deep" / "nested" / "exports"

        with patch("envcrypt.export.append_audit_entry"):
            export_env("prod", out_dir, base_dir=tmp_path)

        assert out_dir.exists()

    def test_appends_audit_entry(self, tmp_path):
        _make_vault(tmp_path, "dev")
        with patch("envcrypt.export.append_audit_entry") as mock_audit:
            export_env("dev", tmp_path / "out", base_dir=tmp_path)
        mock_audit.assert_called_once()
        entry = mock_audit.call_args[0][0]
        assert entry["action"] == "export"
        assert entry["name"] == "dev"


# ---------------------------------------------------------------------------
# import_env
# ---------------------------------------------------------------------------


class TestImportEnv:
    def test_raises_when_source_missing(self, tmp_path):
        with pytest.raises(ExportError, match="Source file not found"):
            import_env(tmp_path / "nope.age", "dev", base_dir=tmp_path)

    def test_raises_when_dest_exists_and_no_overwrite(self, tmp_path):
        _make_vault(tmp_path, "staging")
        src = tmp_path / "staging.age"
        src.write_bytes(b"data")
        with pytest.raises(ExportError, match="already exists"):
            with patch("envcrypt.export.append_audit_entry"):
                import_env(src, "staging", base_dir=tmp_path, overwrite=False)

    def test_imports_when_overwrite_true(self, tmp_path):
        _make_vault(tmp_path, "staging")
        src = tmp_path / "new_staging.age"
        src.write_bytes(b"new-data")
        with patch("envcrypt.export.append_audit_entry"):
            dest = import_env(src, "staging", base_dir=tmp_path, overwrite=True)
        assert dest.read_bytes() == b"new-data"

    def test_imports_new_file(self, tmp_path):
        src = tmp_path / "fresh.age"
        src.write_bytes(b"fresh")
        with patch("envcrypt.export.append_audit_entry"):
            dest = import_env(src, "fresh", base_dir=tmp_path)
        assert dest.exists()


# ---------------------------------------------------------------------------
# list_exports
# ---------------------------------------------------------------------------


class TestListExports:
    def test_returns_empty_when_vault_missing(self, tmp_path):
        assert list_exports(base_dir=tmp_path) == {}

    def test_returns_mapping_of_names_to_paths(self, tmp_path):
        _make_vault(tmp_path, "dev", "staging", "prod")
        result = list_exports(base_dir=tmp_path)
        assert set(result.keys()) == {"dev", "staging", "prod"}
        for path in result.values():
            assert path.suffix == ".age"

    def test_ignores_non_age_files(self, tmp_path):
        vault = _make_vault(tmp_path, "dev")
        (vault / "README.txt").write_text("ignore me")
        result = list_exports(base_dir=tmp_path)
        assert "README" not in result
        assert "dev" in result
