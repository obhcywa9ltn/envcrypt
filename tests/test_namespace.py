"""Tests for envcrypt.namespace."""
import json
import pytest
from pathlib import Path
from envcrypt.namespace import (
    NamespaceError, get_namespaces_path, load_namespaces, save_namespaces,
    add_to_namespace, remove_from_namespace, list_namespaces,
)


def test_get_namespaces_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_namespaces_path() == tmp_path / ".envcrypt" / "namespaces.json"


def test_get_namespaces_path_uses_base_dir(tmp_path):
    assert get_namespaces_path(tmp_path) == tmp_path / ".envcrypt" / "namespaces.json"


def test_load_namespaces_returns_empty_when_missing(tmp_path):
    assert load_namespaces(tmp_path) == {}


def test_load_namespaces_parses_valid_file(tmp_path):
    p = get_namespaces_path(tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"prod": [".env.prod"]}))
    assert load_namespaces(tmp_path) == {"prod": [".env.prod"]}


def test_load_namespaces_raises_on_invalid_json(tmp_path):
    p = get_namespaces_path(tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(NamespaceError, match="Invalid"):
        load_namespaces(tmp_path)


def test_load_namespaces_raises_when_root_not_dict(tmp_path):
    p = get_namespaces_path(tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(["a", "b"]))
    with pytest.raises(NamespaceError, match="JSON object"):
        load_namespaces(tmp_path)


def test_add_to_namespace_creates_entry(tmp_path):
    result = add_to_namespace("staging", ".env.staging", tmp_path)
    assert ".env.staging" in result["staging"]


def test_add_to_namespace_raises_on_duplicate(tmp_path):
    add_to_namespace("staging", ".env.staging", tmp_path)
    with pytest.raises(NamespaceError, match="already in namespace"):
        add_to_namespace("staging", ".env.staging", tmp_path)


def test_remove_from_namespace_removes_entry(tmp_path):
    add_to_namespace("prod", ".env.prod", tmp_path)
    result = remove_from_namespace("prod", ".env.prod", tmp_path)
    assert "prod" not in result


def test_remove_from_namespace_raises_when_missing(tmp_path):
    with pytest.raises(NamespaceError, match="not found"):
        remove_from_namespace("prod", ".env.prod", tmp_path)


def test_list_namespaces_returns_all(tmp_path):
    add_to_namespace("a", "f1", tmp_path)
    add_to_namespace("b", "f2", tmp_path)
    ns = list_namespaces(tmp_path)
    assert "a" in ns and "b" in ns
