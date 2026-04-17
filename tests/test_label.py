"""Tests for envcrypt.label."""
import json
import pytest
from pathlib import Path
from envcrypt.label import (
    LabelError,
    get_labels_path,
    load_labels,
    save_labels,
    add_label,
    remove_label,
    get_label,
)


def test_get_labels_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_labels_path() == tmp_path / ".envcrypt" / "labels.json"


def test_get_labels_path_uses_base_dir(tmp_path):
    assert get_labels_path(tmp_path) == tmp_path / ".envcrypt" / "labels.json"


def test_load_labels_returns_empty_when_missing(tmp_path):
    assert load_labels(tmp_path) == {}


def test_load_labels_parses_valid_file(tmp_path):
    data = {"prod": [".env.prod"], "dev": [".env"]}
    p = tmp_path / ".envcrypt" / "labels.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(data))
    assert load_labels(tmp_path) == data


def test_load_labels_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "labels.json"
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(LabelError, match="Invalid labels file"):
        load_labels(tmp_path)


def test_load_labels_raises_when_root_is_not_dict(tmp_path):
    p = tmp_path / ".envcrypt" / "labels.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(["a", "b"]))
    with pytest.raises(LabelError, match="JSON object"):
        load_labels(tmp_path)


def test_add_label_creates_entry(tmp_path):
    result = add_label("staging", [".env.staging"], tmp_path)
    assert result["staging"] == [".env.staging"]


def test_add_label_raises_on_duplicate(tmp_path):
    add_label("staging", [".env.staging"], tmp_path)
    with pytest.raises(LabelError, match="already exists"):
        add_label("staging", [".env.other"], tmp_path)


def test_remove_label_deletes_entry(tmp_path):
    add_label("staging", [".env.staging"], tmp_path)
    result = remove_label("staging", tmp_path)
    assert "staging" not in result


def test_remove_label_raises_when_missing(tmp_path):
    with pytest.raises(LabelError, match="not found"):
        remove_label("ghost", tmp_path)


def test_get_label_returns_files(tmp_path):
    add_label("prod", [".env.prod", ".env.secrets"], tmp_path)
    assert get_label("prod", tmp_path) == [".env.prod", ".env.secrets"]


def test_get_label_raises_when_missing(tmp_path):
    with pytest.raises(LabelError, match="not found"):
        get_label("nope", tmp_path)
