"""Tests for envcrypt.watch."""

from __future__ import annotations

import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envcrypt.watch import WatchError, get_mtime, watch_env_file


# ---------------------------------------------------------------------------
# get_mtime
# ---------------------------------------------------------------------------

class TestGetMtime:
    def test_returns_float_for_existing_file(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("KEY=value")
        result = get_mtime(f)
        assert isinstance(result, float)

    def test_returns_none_for_missing_file(self, tmp_path):
        result = get_mtime(tmp_path / "nonexistent.env")
        assert result is None


# ---------------------------------------------------------------------------
# watch_env_file
# ---------------------------------------------------------------------------

class TestWatchEnvFile:
    def test_raises_when_env_file_missing(self, tmp_path):
        with pytest.raises(WatchError, match="env file not found"):
            watch_env_file(tmp_path / "missing.env", on_change=MagicMock(), stop_after=0)

    def test_calls_on_change_when_file_modified(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=original")

        callback = MagicMock()
        mtimes = [1000.0, 1000.0, 1001.0]  # third poll detects a change
        mtime_iter = iter(mtimes)

        def fake_sleep(_interval):
            pass

        def fake_get_mtime(_path):
            try:
                return next(mtime_iter)
            except StopIteration:
                return 1001.0

        with patch("envcrypt.watch.time.sleep", side_effect=fake_sleep), \
             patch("envcrypt.watch.get_mtime", side_effect=fake_get_mtime):
            count = watch_env_file(env_file, on_change=callback, poll_interval=0.0, stop_after=1)

        assert count == 1
        callback.assert_called_once_with(env_file)

    def test_stops_after_n_changes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value")

        callback = MagicMock()
        # Alternate mtimes so every poll looks like a change
        call_count = 0

        def alternating_mtime(_path):
            nonlocal call_count
            call_count += 1
            return float(call_count)

        with patch("envcrypt.watch.time.sleep"), \
             patch("envcrypt.watch.get_mtime", side_effect=alternating_mtime):
            count = watch_env_file(env_file, on_change=callback, poll_interval=0.0, stop_after=3)

        assert count == 3
        assert callback.call_count == 3

    def test_handles_file_temporarily_deleted(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value")

        callback = MagicMock()
        # None simulates deletion; then file reappears with new mtime
        responses = [1000.0, None, 1002.0]
        resp_iter = iter(responses)

        def fake_get_mtime(_path):
            try:
                return next(resp_iter)
            except StopIteration:
                return 1002.0

        with patch("envcrypt.watch.time.sleep"), \
             patch("envcrypt.watch.get_mtime", side_effect=fake_get_mtime):
            count = watch_env_file(env_file, on_change=callback, poll_interval=0.0, stop_after=1)

        assert count == 1
