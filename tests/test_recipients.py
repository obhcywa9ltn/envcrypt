"""Tests for envcrypt.recipients module."""

import json
from pathlib import Path

import pytest

from envcrypt.recipients import (
    RecipientsError,
    add_recipient,
    list_public_keys,
    load_recipients,
    remove_recipient,
    save_recipients,
)

VALID_KEY_A = "age1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
VALID_KEY_B = "age1bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


class TestLoadRecipients:
    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        result = load_recipients(tmp_path / "recipients.json")
        assert result == {}

    def test_loads_valid_file(self, tmp_path):
        f = tmp_path / "recipients.json"
        f.write_text(json.dumps({"alice": VALID_KEY_A}))
        assert load_recipients(f) == {"alice": VALID_KEY_A}

    def test_raises_on_invalid_json(self, tmp_path):
        f = tmp_path / "recipients.json"
        f.write_text("not json")
        with pytest.raises(RecipientsError, match="Invalid recipients file"):
            load_recipients(f)

    def test_raises_when_root_is_not_dict(self, tmp_path):
        f = tmp_path / "recipients.json"
        f.write_text(json.dumps(["alice", "bob"]))
        with pytest.raises(RecipientsError, match="JSON object"):
            load_recipients(f)


class TestSaveRecipients:
    def test_creates_parent_dirs_and_saves(self, tmp_path):
        f = tmp_path / "sub" / "recipients.json"
        save_recipients({"alice": VALID_KEY_A}, f)
        assert f.exists()
        assert json.loads(f.read_text()) == {"alice": VALID_KEY_A}


class TestAddRecipient:
    def test_adds_new_recipient(self, tmp_path):
        f = tmp_path / "recipients.json"
        add_recipient("alice", VALID_KEY_A, f)
        assert load_recipients(f)["alice"] == VALID_KEY_A

    def test_updates_existing_recipient(self, tmp_path):
        f = tmp_path / "recipients.json"
        add_recipient("alice", VALID_KEY_A, f)
        add_recipient("alice", VALID_KEY_B, f)
        assert load_recipients(f)["alice"] == VALID_KEY_B

    def test_raises_on_invalid_public_key(self, tmp_path):
        f = tmp_path / "recipients.json"
        with pytest.raises(RecipientsError, match="Invalid age public key"):
            add_recipient("alice", "ssh-rsa AAAA", f)


class TestRemoveRecipient:
    def test_removes_existing_recipient(self, tmp_path):
        f = tmp_path / "recipients.json"
        add_recipient("alice", VALID_KEY_A, f)
        remove_recipient("alice", f)
        assert "alice" not in load_recipients(f)

    def test_raises_when_alias_not_found(self, tmp_path):
        f = tmp_path / "recipients.json"
        with pytest.raises(RecipientsError, match="not found"):
            remove_recipient("ghost", f)


class TestListPublicKeys:
    def test_returns_all_keys(self, tmp_path):
        f = tmp_path / "recipients.json"
        add_recipient("alice", VALID_KEY_A, f)
        add_recipient("bob", VALID_KEY_B, f)
        keys = list_public_keys(f)
        assert VALID_KEY_A in keys
        assert VALID_KEY_B in keys

    def test_returns_empty_list_when_no_recipients(self, tmp_path):
        f = tmp_path / "recipients.json"
        assert list_public_keys(f) == []
