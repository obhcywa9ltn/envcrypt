"""Tests for envcrypt.comment."""
import json
import pytest
from pathlib import Path
from envcrypt.comment import (
    CommentError,
    get_comments_path,
    load_comments,
    save_comments,
    add_comment,
    remove_comment,
    get_comment,
)


def test_get_comments_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_comments_path() == tmp_path / ".envcrypt" / "comments.json"


def test_get_comments_path_uses_base_dir(tmp_path):
    assert get_comments_path(str(tmp_path)) == tmp_path / ".envcrypt" / "comments.json"


def test_load_comments_returns_empty_when_missing(tmp_path):
    assert load_comments(str(tmp_path)) == {}


def test_load_comments_parses_valid_file(tmp_path):
    data = {"API_KEY": "Primary API key"}
    p = tmp_path / ".envcrypt" / "comments.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(data))
    assert load_comments(str(tmp_path)) == data


def test_load_comments_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".envcrypt" / "comments.json"
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(CommentError):
        load_comments(str(tmp_path))


def test_load_comments_raises_when_root_not_dict(tmp_path):
    p = tmp_path / ".envcrypt" / "comments.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(["a", "b"]))
    with pytest.raises(CommentError):
        load_comments(str(tmp_path))


def test_add_comment_creates_entry(tmp_path):
    result = add_comment("DB_URL", "Database connection string", str(tmp_path))
    assert result["DB_URL"] == "Database connection string"


def test_add_comment_raises_on_empty_key(tmp_path):
    with pytest.raises(CommentError):
        add_comment("", "some comment", str(tmp_path))


def test_add_comment_overwrites_existing(tmp_path):
    add_comment("KEY", "old", str(tmp_path))
    result = add_comment("KEY", "new", str(tmp_path))
    assert result["KEY"] == "new"


def test_remove_comment_deletes_entry(tmp_path):
    add_comment("KEY", "desc", str(tmp_path))
    result = remove_comment("KEY", str(tmp_path))
    assert "KEY" not in result


def test_remove_comment_raises_when_missing(tmp_path):
    with pytest.raises(CommentError):
        remove_comment("NONEXISTENT", str(tmp_path))


def test_get_comment_returns_value(tmp_path):
    add_comment("X", "hello", str(tmp_path))
    assert get_comment("X", str(tmp_path)) == "hello"


def test_get_comment_returns_none_when_absent(tmp_path):
    assert get_comment("MISSING", str(tmp_path)) is None
