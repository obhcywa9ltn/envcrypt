"""Tests for envcrypt.quota."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcrypt.quota import (
    QuotaError,
    check_quota,
    get_quota_path,
    load_quota,
    save_quota,
    set_limit,
    DEFAULT_QUOTA,
)


def test_get_quota_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert get_quota_path() == tmp_path / ".envcrypt_quota.json"


def test_get_quota_path_uses_base_dir(tmp_path):
    assert get_quota_path(tmp_path) == tmp_path / ".envcrypt_quota.json"


def test_load_quota_returns_default_when_missing(tmp_path):
    data = load_quota(tmp_path)
    assert data == {"limit": DEFAULT_QUOTA}


def test_load_quota_parses_valid_file(tmp_path):
    get_quota_path(tmp_path).write_text(json.dumps({"limit": 10}))
    assert load_quota(tmp_path) == {"limit": 10}


def test_load_quota_raises_on_invalid_json(tmp_path):
    get_quota_path(tmp_path).write_text("not json")
    with pytest.raises(QuotaError, match="Invalid quota file"):
        load_quota(tmp_path)


def test_load_quota_raises_when_root_not_dict(tmp_path):
    get_quota_path(tmp_path).write_text(json.dumps([1, 2, 3]))
    with pytest.raises(QuotaError, match="JSON object"):
        load_quota(tmp_path)


def test_save_quota_writes_file(tmp_path):
    save_quota({"limit": 20}, tmp_path)
    assert json.loads(get_quota_path(tmp_path).read_text()) == {"limit": 20}


def test_set_limit_updates_value(tmp_path):
    set_limit(15, tmp_path)
    assert load_quota(tmp_path)["limit"] == 15


def test_set_limit_raises_on_zero(tmp_path):
    with pytest.raises(QuotaError, match="positive integer"):
        set_limit(0, tmp_path)


def test_check_quota_returns_count_and_limit(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "a.age").write_text("x")
    (vault / "b.age").write_text("x")
    count, limit = check_quota(vault, tmp_path)
    assert count == 2
    assert limit == DEFAULT_QUOTA


def test_check_quota_raises_when_exceeded(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    set_limit(1, tmp_path)
    for i in range(3):
        (vault / f"{i}.age").write_text("x")
    with pytest.raises(QuotaError, match="exceeds quota"):
        check_quota(vault, tmp_path)


def test_check_quota_returns_zero_when_vault_missing(tmp_path):
    count, limit = check_quota(tmp_path / "nonexistent", tmp_path)
    assert count == 0
