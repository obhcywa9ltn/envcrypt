"""Integration tests for the share CLI commands (push -> ls -> pull roundtrip)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envcrypt.cli_share import share_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_push_ls_roundtrip(runner, tmp_path):
    """push writes files that ls then discovers."""
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hunter2")
    share_dir = tmp_path / "shares"

    alice_out = share_dir / ".env.alice.age"

    def fake_share_with(ef, names, dest, base_dir=None):
        dest.mkdir(parents=True, exist_ok=True)
        for n in names:
            (dest / f"{ef.stem}.{n}.age").write_bytes(b"encrypted")
        return {n: dest / f"{ef.stem}.{n}.age" for n in names}

    with patch("envcrypt.cli_share.share_with", side_effect=fake_share_with):
        push_result = runner.invoke(
            share_group,
            ["push", str(env_file), "alice", "--dest", str(share_dir)],
        )
    assert push_result.exit_code == 0

    ls_result = runner.invoke(share_group, ["ls", "--dir", str(share_dir)])
    assert ls_result.exit_code == 0
    assert ".env.alice.age" in ls_result.output


def test_pull_decrypts_to_dest(runner, tmp_path):
    """pull writes the decrypted file to the specified destination."""
    shared = tmp_path / "file.age"
    shared.write_bytes(b"encrypted")
    key = tmp_path / "key.txt"
    key.write_text("AGE-SECRET-KEY-1")
    dest = tmp_path / "received" / ".env"

    def fake_receive(sf, kf, d):
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text("SECRET=hunter2")
        return d

    with patch("envcrypt.cli_share.receive_share", side_effect=fake_receive):
        result = runner.invoke(
            share_group,
            ["pull", str(shared), str(dest), "--key", str(key)],
        )
    assert result.exit_code == 0
    assert str(dest) in result.output
