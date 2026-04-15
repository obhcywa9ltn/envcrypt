"""Tests for envcrypt.hook"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from envcrypt.hook import (
    HOOK_MARKER,
    HookError,
    get_hook_path,
    get_hooks_dir,
    install_hook,
    is_hook_installed,
    remove_hook,
)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal fake git repo with a hooks directory."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# get_hooks_dir / get_hook_path
# ---------------------------------------------------------------------------

def test_get_hooks_dir_returns_correct_path(git_repo: Path) -> None:
    assert get_hooks_dir(str(git_repo)) == git_repo / ".git" / "hooks"


def test_get_hook_path_returns_pre_commit(git_repo: Path) -> None:
    assert get_hook_path(str(git_repo)) == git_repo / ".git" / "hooks" / "pre-commit"


# ---------------------------------------------------------------------------
# install_hook
# ---------------------------------------------------------------------------

def test_install_hook_creates_file(git_repo: Path) -> None:
    path = install_hook(str(git_repo))
    assert path.exists()
    assert HOOK_MARKER in path.read_text()


def test_install_hook_makes_file_executable(git_repo: Path) -> None:
    path = install_hook(str(git_repo))
    mode = path.stat().st_mode
    assert mode & stat.S_IXUSR


def test_install_hook_is_idempotent(git_repo: Path) -> None:
    install_hook(str(git_repo))
    install_hook(str(git_repo))
    content = get_hook_path(str(git_repo)).read_text()
    assert content.count(HOOK_MARKER) == 1


def test_install_hook_appends_to_existing_hook(git_repo: Path) -> None:
    hook = get_hook_path(str(git_repo))
    hook.write_text("#!/bin/sh\necho hello\n")
    install_hook(str(git_repo))
    content = hook.read_text()
    assert "echo hello" in content
    assert HOOK_MARKER in content


def test_install_hook_raises_when_no_git_dir(tmp_path: Path) -> None:
    with pytest.raises(HookError, match="hooks directory not found"):
        install_hook(str(tmp_path))


# ---------------------------------------------------------------------------
# is_hook_installed
# ---------------------------------------------------------------------------

def test_is_hook_installed_returns_false_when_missing(git_repo: Path) -> None:
    assert is_hook_installed(str(git_repo)) is False


def test_is_hook_installed_returns_true_after_install(git_repo: Path) -> None:
    install_hook(str(git_repo))
    assert is_hook_installed(str(git_repo)) is True


def test_is_hook_installed_returns_false_for_foreign_hook(git_repo: Path) -> None:
    hook = get_hook_path(str(git_repo))
    hook.write_text("#!/bin/sh\necho other hook\n")
    assert is_hook_installed(str(git_repo)) is False


# ---------------------------------------------------------------------------
# remove_hook
# ---------------------------------------------------------------------------

def test_remove_hook_returns_false_when_not_installed(git_repo: Path) -> None:
    assert remove_hook(str(git_repo)) is False


def test_remove_hook_removes_file_when_only_envcrypt(git_repo: Path) -> None:
    install_hook(str(git_repo))
    result = remove_hook(str(git_repo))
    assert result is True
    assert not get_hook_path(str(git_repo)).exists()


def test_remove_hook_preserves_other_content(git_repo: Path) -> None:
    hook = get_hook_path(str(git_repo))
    hook.write_text("#!/bin/sh\necho hello\n")
    install_hook(str(git_repo))
    remove_hook(str(git_repo))
    content = hook.read_text()
    assert "echo hello" in content
    assert HOOK_MARKER not in content


def test_remove_hook_returns_false_when_hook_file_missing(git_repo: Path) -> None:
    assert remove_hook(str(git_repo)) is False
