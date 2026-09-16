"""Git worktree status facts (PLAN Sections 21, 59; TASKS T004).

`WorktreeStatus` exposes the raw staged/unstaged/untracked/ignored facts a
dirty-start preflight (owned by a later TASK's orchestration, PLAN Section 59)
needs, and makes worktree/index divergence observable (TASKS T004 acceptance
criteria: "Worktree/index divergence is observable"). It does not itself
decide whether an Attempt may start; that decision belongs to the
Orchestrator/T005.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WorktreeStatus(BaseModel):
    """Structured `git status` facts for one repository at one point in time.

    A path may appear in both `staged_paths` and `unstaged_paths` (e.g. `git
    add`, then a further edit): that overlap is precisely the worktree/index
    divergence this model makes observable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    staged_paths: tuple[str, ...] = ()
    unstaged_paths: tuple[str, ...] = ()
    untracked_paths: tuple[str, ...] = ()
    ignored_paths: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        """No pre-existing tracked, staged, or untracked (non-ignored) changes.

        Ignored files never make a repository dirty (SPEC Section 12 /
        PLAN Section 23: ignored files are not implicitly part of the
        candidate).
        """
        return not (self.staged_paths or self.unstaged_paths or self.untracked_paths)

    @property
    def has_index_worktree_divergence(self) -> bool:
        """Whether any path is both staged and further modified unstaged.

        Proves the candidate must be computed from the full worktree, not
        merely the Git index (PLAN Section 23).
        """
        return bool(set(self.staged_paths) & set(self.unstaged_paths))
