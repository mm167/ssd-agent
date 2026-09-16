from __future__ import annotations

from sdd_agent.domain.models.git_status import WorktreeStatus


def test_empty_status_is_clean() -> None:
    assert WorktreeStatus().is_clean is True


def test_staged_path_is_dirty() -> None:
    assert WorktreeStatus(staged_paths=("a.txt",)).is_clean is False


def test_unstaged_path_is_dirty() -> None:
    assert WorktreeStatus(unstaged_paths=("a.txt",)).is_clean is False


def test_untracked_path_is_dirty() -> None:
    assert WorktreeStatus(untracked_paths=("a.txt",)).is_clean is False


def test_ignored_only_path_is_clean() -> None:
    assert WorktreeStatus(ignored_paths=("build/out.log",)).is_clean is True


def test_no_divergence_when_only_staged() -> None:
    status = WorktreeStatus(staged_paths=("a.txt",))
    assert status.has_index_worktree_divergence is False


def test_no_divergence_when_only_unstaged() -> None:
    status = WorktreeStatus(unstaged_paths=("a.txt",))
    assert status.has_index_worktree_divergence is False


def test_divergence_when_path_staged_and_further_edited_unstaged() -> None:
    status = WorktreeStatus(staged_paths=("a.txt",), unstaged_paths=("a.txt",))
    assert status.has_index_worktree_divergence is True
