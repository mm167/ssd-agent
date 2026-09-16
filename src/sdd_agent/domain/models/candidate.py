"""CandidateSnapshot and CandidateIdentity (PLAN Section 23; TASKS T004).

`CandidateSnapshot` is the authorized repository worktree state relative to
an immutable baseline commit, independent from Git's staging/index state
(PLAN Section 23: "The Git index is not the authority that defines the
candidate."). `CandidateIdentity` is the value validation, review,
READY_TO_COMMIT and human approval are bound to.

T004 owns this shape and its deterministic fingerprint computation (via the
`GitRepository` port and Git CLI adapter). It does not own gate policies or
invalidation rules (T005), nor commit execution (T013).
"""

from __future__ import annotations

import hashlib
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CandidateEntryKind(StrEnum):
    """How one path differs from the baseline (PLAN Section 23).

    Renames are represented as a DELETED entry for the old path plus an
    ADDED entry for the new path; there is no RENAMED kind, so Git rename
    heuristics cannot change candidate identity (PLAN Section 23).
    """

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class CandidateEntry(BaseModel):
    """One path's contribution to a CandidateSnapshot (PLAN Section 23).

    `path` is repository-relative with forward-slash separators. `file_mode`
    and `content_sha256` are `None` exactly when `kind` is DELETED; a
    deletion carries no content or mode to record.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    kind: CandidateEntryKind
    file_mode: str | None = None
    content_sha256: str | None = None

    @model_validator(mode="after")
    def _content_matches_kind(self) -> "CandidateEntry":
        has_mode = self.file_mode is not None
        has_content = self.content_sha256 is not None
        if self.kind is CandidateEntryKind.DELETED:
            if has_mode or has_content:
                raise ValueError("a DELETED CandidateEntry must not carry file_mode/content_sha256")
        else:
            if not has_mode or not has_content:
                raise ValueError(
                    "a non-DELETED CandidateEntry must carry both file_mode and content_sha256"
                )
        return self


class CandidateSnapshot(BaseModel):
    """Deterministic worktree state relative to `baseline_sha` (PLAN Section 23).

    `entries` must already be sorted by `path` (ascending, no duplicates) so
    two snapshots built from the same underlying changes always serialize
    and fingerprint identically (PLAN Section 23: "deterministic ordering").
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_sha: str = Field(min_length=1)
    entries: tuple[CandidateEntry, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _entries_sorted_and_unique(self) -> "CandidateSnapshot":
        paths = [entry.path for entry in self.entries]
        if paths != sorted(paths):
            raise ValueError("CandidateSnapshot.entries must be sorted by path")
        if len(set(paths)) != len(paths):
            raise ValueError("CandidateSnapshot.entries must not contain duplicate paths")
        return self

    def fingerprint(self) -> str:
        """A deterministic content fingerprint of `entries` (PLAN Section 23).

        Independent of `baseline_sha`: `CandidateIdentity` combines this with
        `baseline_sha` separately, matching PLAN's `CandidateIdentity =
        baseline_sha + content_fingerprint(CandidateSnapshot)`.
        """
        digest = hashlib.sha256()
        for entry in self.entries:
            digest.update(entry.path.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(entry.kind.value.encode("utf-8"))
            digest.update(b"\x00")
            digest.update((entry.file_mode or "").encode("utf-8"))
            digest.update(b"\x00")
            digest.update((entry.content_sha256 or "").encode("utf-8"))
            digest.update(b"\x00")
        return digest.hexdigest()


class CandidateIdentity(BaseModel):
    """The identity validation, review, READY_TO_COMMIT and human approval are
    bound to (PLAN Section 23).

    ``same baseline + same canonical CandidateSnapshot -> same CandidateIdentity``
    ``different candidate content/mode/path/deletion -> different CandidateIdentity``
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_sha: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)

    @classmethod
    def from_snapshot(cls, snapshot: CandidateSnapshot) -> "CandidateIdentity":
        return cls(baseline_sha=snapshot.baseline_sha, fingerprint=snapshot.fingerprint())
