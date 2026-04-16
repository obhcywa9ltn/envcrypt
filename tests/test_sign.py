"""Tests for envcrypt.sign."""

import json
import pytest
from pathlib import Path
from envcrypt.sign import (
    SignError,
    get_manifest_path,
    load_manifest,
    save_manifest,
    sign_file,
    verify_signature,
    remove_signature,
)


def test_get_manifest_path_defaults_to_cwd():
    p = get_manifest_path()
    assert p == Path.cwd() / ".envcrypt" / "manifest.json"


def test_get_manifest_path_uses_base_dir(tmp_path):
    p = get_manifest_path(tmp_path)
    assert p == tmp_path / ".envcrypt" / "manifest.json"


def test_load_manifest_returns_empty_when_missing(tmp_path):
    assert load_manifest(tmp_path) == {}


def test_load_manifest_parses_valid_file(tmp_path):
    data = {"foo": "abc123"}
    mp = tmp_path / ".envcrypt" / "manifest.json"
    mp.parent.mkdir(parents=True)
    mp.write_text(json.dumps(data))
    assert load_manifest(tmp_path) == data


def test_load_manifest_raises_on_invalid_json(tmp_path):
    mp = tmp_path / ".envcrypt" / "manifest.json"
    mp.parent.mkdir(parents=True)
    mp.write_text("not json")
    with pytest.raises(SignError, match="Invalid manifest JSON"):
        load_manifest(tmp_path)


def test_load_manifest_raises_when_root_is_not_dict(tmp_path):
    mp = tmp_path / ".envcrypt" / "manifest.json"
    mp.parent.mkdir(parents=True)
    mp.write_text("[1, 2, 3]")
    with pytest.raises(SignError, match="root must be a JSON object"):
        load_manifest(tmp_path)


def test_sign_file_raises_when_missing(tmp_path):
    with pytest.raises(SignError, match="File not found"):
        sign_file(tmp_path / "ghost.env", base_dir=tmp_path)


def test_sign_file_returns_digest_and_stores(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("KEY=val")
    digest = sign_file(f, base_dir=tmp_path)
    assert len(digest) == 64
    manifest = load_manifest(tmp_path)
    assert manifest[str(f)] == digest


def test_verify_signature_returns_true_for_signed_file(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("KEY=val")
    sign_file(f, base_dir=tmp_path)
    assert verify_signature(f, base_dir=tmp_path) is True


def test_verify_signature_returns_false_when_not_signed(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("KEY=val")
    assert verify_signature(f, base_dir=tmp_path) is False


def test_verify_signature_returns_false_when_file_changed(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("KEY=val")
    sign_file(f, base_dir=tmp_path)
    f.write_text("KEY=changed")
    assert verify_signature(f, base_dir=tmp_path) is False


def test_verify_signature_raises_when_file_missing(tmp_path):
    with pytest.raises(SignError, match="File not found"):
        verify_signature(tmp_path / "ghost.env", base_dir=tmp_path)


def test_remove_signature_returns_true_and_removes(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("KEY=val")
    sign_file(f, base_dir=tmp_path)
    assert remove_signature(f, base_dir=tmp_path) is True
    assert str(f) not in load_manifest(tmp_path)


def test_remove_signature_returns_false_when_not_present(tmp_path):
    f = tmp_path / "test.env"
    f.write_text("KEY=val")
    assert remove_signature(f, base_dir=tmp_path) is False
