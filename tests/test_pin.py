"""Tests for envcrypt.pin."""
import json
import pytest
from pathlib import Path
from envcrypt.pin import (
    PinError,
    get_pins_path,
    load_pins,
    save_pins,
    pin_file,
    check_pin,
    remove_pin,
)


def test_get_pins_path_defaults_to_cwd():
    p = get_pins_path()
    assert p.parent == Path.cwd()
    assert p.name == ".envcrypt_pins.json"


def test_get_pins_path_uses_base_dir(tmp_path):
    assert get_pins_path(tmp_path) == tmp_path / ".envcrypt_pins.json"


def test_load_pins_returns_empty_when_missing(tmp_path):
    assert load_pins(tmp_path) == {}


def test_load_pins_parses_valid_file(tmp_path):
    data = {"dev": "abc123"}
    (tmp_path / ".envcrypt_pins.json").write_text(json.dumps(data))
    assert load_pins(tmp_path) == data


def test_load_pins_raises_on_invalid_json(tmp_path):
    (tmp_path / ".envcrypt_pins.json").write_text("not json")
    with pytest.raises(PinError, match="Invalid pins file"):
        load_pins(tmp_path)


def test_load_pins_raises_when_root_not_dict(tmp_path):
    (tmp_path / ".envcrypt_pins.json").write_text("[1,2,3]")
    with pytest.raises(PinError, match="root must be a JSON object"):
        load_pins(tmp_path)


def test_save_and_load_roundtrip(tmp_path):
    pins = {"prod": "deadbeef"}
    save_pins(pins, tmp_path)
    assert load_pins(tmp_path) == pins


def test_pin_file_stores_hash(tmp_path):
    enc = tmp_path / "secret.env.age"
    enc.write_bytes(b"encrypted content")
    digest = pin_file("dev", enc, tmp_path)
    assert len(digest) == 64
    assert load_pins(tmp_path)["dev"] == digest


def test_pin_file_raises_when_missing(tmp_path):
    with pytest.raises(PinError, match="Encrypted file not found"):
        pin_file("dev", tmp_path / "ghost.age", tmp_path)


def test_check_pin_returns_true_when_matching(tmp_path):
    enc = tmp_path / "secret.env.age"
    enc.write_bytes(b"data")
    pin_file("dev", enc, tmp_path)
    assert check_pin("dev", enc, tmp_path) is True


def test_check_pin_returns_false_when_changed(tmp_path):
    enc = tmp_path / "secret.env.age"
    enc.write_bytes(b"original")
    pin_file("dev", enc, tmp_path)
    enc.write_bytes(b"modified")
    assert check_pin("dev", enc, tmp_path) is False


def test_check_pin_returns_false_when_file_missing(tmp_path):
    enc = tmp_path / "secret.env.age"
    enc.write_bytes(b"data")
    pin_file("dev", enc, tmp_path)
    enc.unlink()
    assert check_pin("dev", enc, tmp_path) is False


def test_check_pin_raises_when_no_pin(tmp_path):
    enc = tmp_path / "secret.env.age"
    enc.write_bytes(b"data")
    with pytest.raises(PinError, match="No pin found"):
        check_pin("unknown", enc, tmp_path)


def test_remove_pin_returns_true_when_present(tmp_path):
    enc = tmp_path / "f.age"
    enc.write_bytes(b"x")
    pin_file("dev", enc, tmp_path)
    assert remove_pin("dev", tmp_path) is True
    assert "dev" not in load_pins(tmp_path)


def test_remove_pin_returns_false_when_absent(tmp_path):
    assert remove_pin("nope", tmp_path) is False
