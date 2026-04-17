"""Tests for envcrypt.alias."""
import json
import pytest
from pathlib import Path
from envcrypt.alias import (
    AliasError,
    get_aliases_path,
    load_aliases,
    save_aliases,
    add_alias,
    remove_alias,
    resolve_alias,
)


def test_get_aliases_path_defaults_to_cwd(tmp_path):
    p = get_aliases_path(tmp_path)
    assert p == tmp_path / ".envcrypt" / "aliases.json"


def test_get_aliases_path_uses_base_dir(tmp_path):
    p = get_aliases_path(tmp_path / "sub")
    assert p == tmp_path / "sub" / ".envcrypt" / "aliases.json"


def test_load_aliases_returns_empty_when_missing(tmp_path):
    assert load_aliases(tmp_path) == {}


def test_load_aliases_parses_valid_file(tmp_path):
    path = get_aliases_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"prod": ".env.production"}))
    assert load_aliases(tmp_path) == {"prod": ".env.production"}


def test_load_aliases_raises_on_invalid_json(tmp_path):
    path = get_aliases_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("not json")
    with pytest.raises(AliasError, match="Invalid aliases file"):
        load_aliases(tmp_path)


def test_load_aliases_raises_when_root_not_dict(tmp_path):
    path = get_aliases_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(["a", "b"]))
    with pytest.raises(AliasError, match="JSON object"):
        load_aliases(tmp_path)


def test_add_alias_saves_entry(tmp_path):
    result = add_alias("staging", ".env.staging", tmp_path)
    assert result["staging"] == ".env.staging"
    assert load_aliases(tmp_path)["staging"] == ".env.staging"


def test_add_alias_raises_on_duplicate(tmp_path):
    add_alias("dev", ".env.dev", tmp_path)
    with pytest.raises(AliasError, match="already exists"):
        add_alias("dev", ".env.dev2", tmp_path)


def test_remove_alias_deletes_entry(tmp_path):
    add_alias("qa", ".env.qa", tmp_path)
    result = remove_alias("qa", tmp_path)
    assert "qa" not in result
    assert "qa" not in load_aliases(tmp_path)


def test_remove_alias_raises_when_not_found(tmp_path):
    with pytest.raises(AliasError, match="not found"):
        remove_alias("ghost", tmp_path)


def test_resolve_alias_returns_target(tmp_path):
    add_alias("prod", ".env.prod", tmp_path)
    assert resolve_alias("prod", tmp_path) == ".env.prod"


def test_resolve_alias_raises_when_not_found(tmp_path):
    with pytest.raises(AliasError, match="not found"):
        resolve_alias("missing", tmp_path)
