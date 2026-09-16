"""`GitRepository` port (PLAN Section 21; TASKS T004).

Exposes Git repository inspection needed for baseline identity, dirty-start
detection, and CandidateSnapshot computation. `GitCliRepository`
(`sdd_agent.adapters.git.cli`) is the concrete V1 implementation, invoking
the `git` executable as a subprocess (PLAN Section 3.1).

This port is inspection-oriented only (TASKS T004 Scope). It does not
perform `commit`, `push`, `reset --hard`, `clean -fd`, or any other
repository mutation; those belong to T013 (and are explicitly excluded from
T004's Future-Task Boundary).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sdd_agent.domain.models.candidate import CandidateSnapshot
from sdd_agent.domain.models.git_status import WorktreeStatus


class GitRepository(ABC):
    """Provider-neutral contract for Git repository inspection."""

    @abstractmethod
    def head_sha(self) -> str:
        """The full current HEAD commit SHA (PLAN Section 22).

        A branch name alone is not a baseline identity because the branch
        can move; callers needing a baseline use this full SHA.
        """

    @abstractmethod
    def current_branch(self) -> str | None:
        """The current branch name, or `None` when HEAD is detached."""

    @abstractmethod
    def worktree_status(self) -> WorktreeStatus:
        """The current staged/unstaged/untracked/ignored worktree facts."""

    @abstractmethod
    def candidate_snapshot(self, baseline_sha: str) -> CandidateSnapshot:
        """The deterministic worktree state relative to `baseline_sha`
        (PLAN Section 23), independent from the current staging/index
        arrangement.

        Recalculation reconstructs the actual current snapshot from the
        worktree; it does not merely inspect a previously recorded
        fingerprint or the Git index (PLAN Section 24).
        """
