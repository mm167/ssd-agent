from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from sdd_agent.adapters.git.cli import GitCliRepository
from sdd_agent.diagnostics.errors import GitOperationError
from sdd_agent.domain.models.candidate import CandidateEntryKind


def _git(args: list[str], cwd: Path) -> bytes:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True)
    return result.stdout


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q"], cwd=path)
    _git(["config", "user.name", "Test"], cwd=path)
    _git(["config", "user.email", "test@example.com"], cwd=path)
    _git(["config", "core.autocrlf", "false"], cwd=path)


def _commit_all(path: Path, message: str) -> None:
    _git(["add", "-A"], cwd=path)
    _git(["commit", "-q", "-m", message], cwd=path)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "repo"
    _init_repo(repo_path)
    (repo_path / "tracked.txt").write_bytes(b"original content\n")
    (repo_path / ".gitignore").write_bytes(b"ignored/\n*.ignored\n")
    _commit_all(repo_path, "initial commit")
    return repo_path


def _repo(repo_path: Path) -> GitCliRepository:
    return GitCliRepository(repo_path)


# -- baseline identity ----------------------------------------------------


def test_head_sha_is_full_40_char_sha(repo: Path) -> None:
    sha = _repo(repo).head_sha()
    assert len(sha) == 40
    assert all(c in "0123456789abcdef" for c in sha)


def test_current_branch_returns_checked_out_branch(repo: Path) -> None:
    branch = _repo(repo).current_branch()
    assert branch is not None


def test_current_branch_is_none_when_detached(repo: Path) -> None:
    git_repo = _repo(repo)
    head = git_repo.head_sha()
    _git(["checkout", "-q", head], cwd=repo)

    assert git_repo.current_branch() is None


# -- clean / dirty detection -----------------------------------------------


def test_clean_repository_is_clean_with_empty_candidate(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert status.is_clean is True
    assert snapshot.entries == ()
    assert snapshot.baseline_sha == baseline


def test_candidate_stable_across_repeated_calls_when_nothing_changes(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()

    first = git_repo.candidate_snapshot(baseline)
    second = git_repo.candidate_snapshot(baseline)

    assert first.fingerprint() == second.fingerprint()


# -- tracked modifications --------------------------------------------------


def test_unstaged_tracked_modification_is_modified_entry(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    new_content = b"unstaged edit\n"
    (repo / "tracked.txt").write_bytes(new_content)

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "tracked.txt" in status.unstaged_paths
    assert status.staged_paths == ()
    (entry,) = snapshot.entries
    assert entry.path == "tracked.txt"
    assert entry.kind is CandidateEntryKind.MODIFIED
    assert entry.content_sha256 == _sha256(new_content)


def test_staged_tracked_modification_is_modified_entry(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    new_content = b"staged edit\n"
    (repo / "tracked.txt").write_bytes(new_content)
    _git(["add", "tracked.txt"], cwd=repo)

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "tracked.txt" in status.staged_paths
    assert status.unstaged_paths == ()
    (entry,) = snapshot.entries
    assert entry.content_sha256 == _sha256(new_content)


def test_staged_change_plus_further_unstaged_edit_uses_final_worktree_content(repo: Path) -> None:
    """Proves candidate reflects the full worktree, not merely the index."""
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()

    (repo / "tracked.txt").write_bytes(b"staged version\n")
    _git(["add", "tracked.txt"], cwd=repo)
    final_content = b"further unstaged edit on top of staged version\n"
    (repo / "tracked.txt").write_bytes(final_content)

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert status.has_index_worktree_divergence is True
    (entry,) = snapshot.entries
    assert entry.kind is CandidateEntryKind.MODIFIED
    assert entry.content_sha256 == _sha256(final_content)


def test_candidate_identity_unchanged_when_content_reverted_to_baseline(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    clean_fingerprint = git_repo.candidate_snapshot(baseline).fingerprint()

    (repo / "tracked.txt").write_bytes(b"temporary edit\n")
    assert git_repo.candidate_snapshot(baseline).fingerprint() != clean_fingerprint

    (repo / "tracked.txt").write_bytes(b"original content\n")
    reverted_fingerprint = git_repo.candidate_snapshot(baseline).fingerprint()

    assert reverted_fingerprint == clean_fingerprint


# -- deletions ---------------------------------------------------------------


def test_unstaged_deletion_is_deleted_entry(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    (repo / "tracked.txt").unlink()

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "tracked.txt" in status.unstaged_paths
    (entry,) = snapshot.entries
    assert entry.kind is CandidateEntryKind.DELETED
    assert entry.file_mode is None
    assert entry.content_sha256 is None


def test_staged_deletion_is_deleted_entry(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    _git(["rm", "-q", "tracked.txt"], cwd=repo)

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "tracked.txt" in status.staged_paths
    (entry,) = snapshot.entries
    assert entry.kind is CandidateEntryKind.DELETED


# -- untracked / ignored -------------------------------------------------


def test_non_ignored_untracked_file_is_added_entry(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    content = b"brand new file\n"
    (repo / "new_file.txt").write_bytes(content)

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "new_file.txt" in status.untracked_paths
    (entry,) = snapshot.entries
    assert entry.path == "new_file.txt"
    assert entry.kind is CandidateEntryKind.ADDED
    assert entry.content_sha256 == _sha256(content)


def test_ignored_file_excluded_from_status_and_candidate(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    (repo / "scratch.ignored").write_bytes(b"should not be tracked\n")

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "scratch.ignored" in status.ignored_paths
    assert "scratch.ignored" not in status.untracked_paths
    assert snapshot.entries == ()


def test_ignore_rule_change_changes_candidate_identity(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    (repo / "scratch.ignored").write_bytes(b"content\n")
    ignored_fingerprint = git_repo.candidate_snapshot(baseline).fingerprint()

    (repo / ".gitignore").write_bytes(b"ignored/\n")  # no longer ignores *.ignored
    _git(["add", ".gitignore"], cwd=repo)
    included_fingerprint = git_repo.candidate_snapshot(baseline).fingerprint()

    assert ignored_fingerprint != included_fingerprint
    paths = {entry.path for entry in git_repo.candidate_snapshot(baseline).entries}
    assert "scratch.ignored" in paths


# -- rename representation ----------------------------------------------


def test_rename_is_delete_plus_add_not_a_rename_entry(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    _git(["mv", "tracked.txt", "renamed.txt"], cwd=repo)

    snapshot = git_repo.candidate_snapshot(baseline)

    kinds_by_path = {entry.path: entry.kind for entry in snapshot.entries}
    assert kinds_by_path["tracked.txt"] is CandidateEntryKind.DELETED
    assert kinds_by_path["renamed.txt"] is CandidateEntryKind.ADDED


# -- binary content -----------------------------------------------------


def test_binary_untracked_file_content_identity(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    binary_content = bytes(range(256))
    (repo / "blob.bin").write_bytes(binary_content)

    snapshot = git_repo.candidate_snapshot(baseline)

    (entry,) = snapshot.entries
    assert entry.content_sha256 == _sha256(binary_content)


# -- path handling --------------------------------------------------------


def test_nested_untracked_file_uses_repo_relative_forward_slash_path(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    nested = repo / "sub" / "dir"
    nested.mkdir(parents=True)
    (nested / "deep.txt").write_bytes(b"deep\n")

    snapshot = git_repo.candidate_snapshot(baseline)

    (entry,) = snapshot.entries
    assert entry.path == "sub/dir/deep.txt"


def test_path_with_spaces_is_parsed_correctly(repo: Path) -> None:
    git_repo = _repo(repo)
    baseline = git_repo.head_sha()
    content = b"spacey\n"
    (repo / "a file with spaces.txt").write_bytes(content)

    status = git_repo.worktree_status()
    snapshot = git_repo.candidate_snapshot(baseline)

    assert "a file with spaces.txt" in status.untracked_paths
    (entry,) = snapshot.entries
    assert entry.path == "a file with spaces.txt"
    assert entry.content_sha256 == _sha256(content)


# -- git failure handling -------------------------------------------------


def test_non_repository_raises_git_operation_error(tmp_path: Path) -> None:
    not_a_repo = tmp_path / "not_a_repo"
    not_a_repo.mkdir()

    with pytest.raises(GitOperationError):
        GitCliRepository(not_a_repo).head_sha()
