import json
import pytest
from pathlib import Path
from envcrypt.access import (
    AccessError,
    get_access_path,
    load_access,
    save_access,
    grant_access,
    revoke_access,
    is_allowed,
)


def test_get_access_path_defaults_to_cwd():
    p = get_access_path()
    assert p == Path.cwd() / ".envcrypt" / "access.json"


def test_get_access_path_uses_base_dir(tmp_path):
    p = get_access_path(str(tmp_path))
    assert p == tmp_path / ".envcrypt" / "access.json"


def test_load_access_returns_empty_when_missing(tmp_path):
    assert load_access(str(tmp_path)) == {}


def test_load_access_parses_valid_file(tmp_path):
    data = {"prod": ["age1abc", "age1def"]}
    p = tmp_path / ".envcrypt" / "access.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(data))
    assert load_access(str(tmp_path)) == data


def test_load_access_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "access.json"
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(AccessError, match="Invalid JSON"):
        load_access(str(tmp_path))


def test_load_access_raises_when_root_not_dict(tmp_path):
    p = tmp_path / ".envcrypt" / "access.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(["list"]))
    with pytest.raises(AccessError, match="root must be a JSON object"):
        load_access(str(tmp_path))


def test_grant_access_adds_recipient(tmp_path):
    result = grant_access("prod", "age1abc", str(tmp_path))
    assert "age1abc" in result["prod"]


def test_grant_access_idempotent(tmp_path):
    grant_access("prod", "age1abc", str(tmp_path))
    result = grant_access("prod", "age1abc", str(tmp_path))
    assert result["prod"].count("age1abc") == 1


def test_revoke_access_removes_recipient(tmp_path):
    grant_access("prod", "age1abc", str(tmp_path))
    result = revoke_access("prod", "age1abc", str(tmp_path))
    assert "age1abc" not in result["prod"]


def test_revoke_access_raises_when_not_present(tmp_path):
    with pytest.raises(AccessError, match="not in access list"):
        revoke_access("prod", "age1xyz", str(tmp_path))


def test_is_allowed_true_when_no_restrictions(tmp_path):
    assert is_allowed("staging", "age1abc", str(tmp_path)) is True


def test_is_allowed_true_when_in_list(tmp_path):
    grant_access("prod", "age1abc", str(tmp_path))
    assert is_allowed("prod", "age1abc", str(tmp_path)) is True


def test_is_allowed_false_when_not_in_list(tmp_path):
    grant_access("prod", "age1abc", str(tmp_path))
    assert is_allowed("prod", "age1other", str(tmp_path)) is False
