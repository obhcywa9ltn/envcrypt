"""Tests for envcrypt.env_group."""
import json
import pytest
from pathlib import Path
from envcrypt.env_group import (
    GroupError,
    get_groups_path,
    load_groups,
    save_groups,
    add_to_group,
    remove_from_group,
    list_groups,
)


def test_get_groups_path_defaults_to_cwd():
    p = get_groups_path()
    assert p == Path.cwd() / ".envcrypt" / "groups.json"


def test_get_groups_path_uses_base_dir(tmp_path):
    p = get_groups_path(str(tmp_path))
    assert p == tmp_path / ".envcrypt" / "groups.json"


def test_load_groups_returns_empty_when_missing(tmp_path):
    assert load_groups(str(tmp_path)) == {}


def test_load_groups_parses_valid_file(tmp_path):
    data = {"backend": ["DB_URL", "SECRET_KEY"]}
    p = tmp_path / ".envcrypt" / "groups.json"
    p.parent.mkdir()
    p.write_text(json.dumps(data))
    assert load_groups(str(tmp_path)) == data


def test_load_groups_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "groups.json"
    p.parent.mkdir()
    p.write_text("not json")
    with pytest.raises(GroupError, match="Invalid JSON"):
        load_groups(str(tmp_path))


def test_load_groups_raises_when_root_not_dict(tmp_path):
    p = tmp_path / ".envcrypt" / "groups.json"
    p.parent.mkdir()
    p.write_text(json.dumps(["a", "b"]))
    with pytest.raises(GroupError, match="root must be a JSON object"):
        load_groups(str(tmp_path))


def test_add_to_group_creates_group(tmp_path):
    result = add_to_group("backend", "DB_URL", str(tmp_path))
    assert result == {"backend": ["DB_URL"]}


def test_add_to_group_appends_key(tmp_path):
    add_to_group("backend", "DB_URL", str(tmp_path))
    result = add_to_group("backend", "SECRET_KEY", str(tmp_path))
    assert result["backend"] == ["DB_URL", "SECRET_KEY"]


def test_add_to_group_raises_on_duplicate(tmp_path):
    add_to_group("backend", "DB_URL", str(tmp_path))
    with pytest.raises(GroupError, match="already in group"):
        add_to_group("backend", "DB_URL", str(tmp_path))


def test_remove_from_group_removes_key(tmp_path):
    add_to_group("backend", "DB_URL", str(tmp_path))
    add_to_group("backend", "SECRET", str(tmp_path))
    result = remove_from_group("backend", "DB_URL", str(tmp_path))
    assert "DB_URL" not in result["backend"]


def test_remove_from_group_deletes_empty_group(tmp_path):
    add_to_group("backend", "DB_URL", str(tmp_path))
    result = remove_from_group("backend", "DB_URL", str(tmp_path))
    assert "backend" not in result


def test_remove_from_group_raises_when_group_missing(tmp_path):
    with pytest.raises(GroupError, match="not found"):
        remove_from_group("missing", "KEY", str(tmp_path))


def test_remove_from_group_raises_when_key_missing(tmp_path):
    add_to_group("backend", "DB_URL", str(tmp_path))
    with pytest.raises(GroupError, match="not in group"):
        remove_from_group("backend", "OTHER", str(tmp_path))


def test_list_groups_returns_all(tmp_path):
    add_to_group("g1", "A", str(tmp_path))
    add_to_group("g2", "B", str(tmp_path))
    groups = list_groups(str(tmp_path))
    assert set(groups.keys()) == {"g1", "g2"}
