"""Tests for envcrypt.env_count."""

from pathlib import Path

import pytest

from envcrypt.env_count import (
    CountError,
    count_keys,
    keys_in_all,
    keys_in_one,
)


@pytest.fixture()
def env_files(tmp_path: Path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    b.write_text("DB_HOST=prod\nAPI_KEY=xyz\n# comment\n\nDB_PORT=5433\n")
    return a, b


def test_raises_when_no_files_provided():
    with pytest.raises(CountError, match="No env files"):
        count_keys([])


def test_raises_when_file_missing(tmp_path: Path):
    missing = tmp_path / "ghost.env"
    with pytest.raises(CountError, match="not found"):
        count_keys([missing])


def test_total_files(env_files):
    a, b = env_files
    result = count_keys([a, b])
    assert result.total_files == 2


def test_total_keys(env_files):
    a, b = env_files
    result = count_keys([a, b])
    # a has 3 keys, b has 3 keys
    assert result.total_keys == 6


def test_unique_keys(env_files):
    a, b = env_files
    result = count_keys([a, b])
    # DB_HOST, DB_PORT, SECRET, API_KEY => 4
    assert result.unique_keys == 4


def test_shared_key_occurrence(env_files):
    a, b = env_files
    result = count_keys([a, b])
    assert result.counts["DB_HOST"].occurrences == 2


def test_unique_key_occurrence(env_files):
    a, b = env_files
    result = count_keys([a, b])
    assert result.counts["SECRET"].occurrences == 1
    assert result.counts["API_KEY"].occurrences == 1


def test_file_list_recorded(env_files):
    a, b = env_files
    result = count_keys([a, b])
    assert str(a) in result.counts["DB_HOST"].files
    assert str(b) in result.counts["DB_HOST"].files


def test_keys_in_all(env_files):
    a, b = env_files
    result = count_keys([a, b])
    common = keys_in_all(result)
    assert set(common) == {"DB_HOST", "DB_PORT"}


def test_keys_in_one(env_files):
    a, b = env_files
    result = count_keys([a, b])
    solo = keys_in_one(result)
    assert set(solo) == {"SECRET", "API_KEY"}


def test_single_file(tmp_path: Path):
    f = tmp_path / "solo.env"
    f.write_text("FOO=1\nBAR=2\n")
    result = count_keys([f])
    assert result.total_files == 1
    assert result.unique_keys == 2
    assert keys_in_all(result) == ["FOO", "BAR"] or set(keys_in_all(result)) == {"FOO", "BAR"}
