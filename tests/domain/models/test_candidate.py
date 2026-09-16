from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models.candidate import (
    CandidateEntry,
    CandidateEntryKind,
    CandidateIdentity,
    CandidateSnapshot,
)

_BASELINE = "a" * 40


def _entry(path: str, *, content: str = "x") -> CandidateEntry:
    return CandidateEntry(
        path=path,
        kind=CandidateEntryKind.MODIFIED,
        file_mode="100644",
        content_sha256=content,
    )


def test_deleted_entry_rejects_content() -> None:
    with pytest.raises(ValidationError):
        CandidateEntry(
            path="a.txt",
            kind=CandidateEntryKind.DELETED,
            content_sha256="deadbeef",
        )


def test_non_deleted_entry_requires_content() -> None:
    with pytest.raises(ValidationError):
        CandidateEntry(path="a.txt", kind=CandidateEntryKind.ADDED)


def test_non_deleted_entry_rejects_missing_file_mode() -> None:
    with pytest.raises(ValidationError):
        CandidateEntry(path="a.txt", kind=CandidateEntryKind.ADDED, content_sha256="deadbeef")


def test_non_deleted_entry_rejects_missing_content_sha256() -> None:
    with pytest.raises(ValidationError):
        CandidateEntry(path="a.txt", kind=CandidateEntryKind.ADDED, file_mode="100644")


def test_non_deleted_entry_with_both_fields_is_valid() -> None:
    entry = CandidateEntry(
        path="a.txt",
        kind=CandidateEntryKind.ADDED,
        file_mode="100644",
        content_sha256="deadbeef",
    )
    assert entry.file_mode == "100644"
    assert entry.content_sha256 == "deadbeef"


def test_deleted_entry_without_content_is_valid() -> None:
    entry = CandidateEntry(path="a.txt", kind=CandidateEntryKind.DELETED)
    assert entry.file_mode is None
    assert entry.content_sha256 is None


def test_deleted_entry_rejects_file_mode_only() -> None:
    with pytest.raises(ValidationError):
        CandidateEntry(path="a.txt", kind=CandidateEntryKind.DELETED, file_mode="100644")


def test_snapshot_rejects_unsorted_entries() -> None:
    with pytest.raises(ValidationError):
        CandidateSnapshot(baseline_sha=_BASELINE, entries=(_entry("b.txt"), _entry("a.txt")))


def test_snapshot_rejects_duplicate_paths() -> None:
    with pytest.raises(ValidationError):
        CandidateSnapshot(
            baseline_sha=_BASELINE,
            entries=(_entry("a.txt", content="1"), _entry("a.txt", content="2")),
        )


def test_empty_snapshot_is_valid() -> None:
    snapshot = CandidateSnapshot(baseline_sha=_BASELINE)
    assert snapshot.entries == ()


def test_fingerprint_deterministic_for_same_entries() -> None:
    entries = (_entry("a.txt"), _entry("b.txt"))
    first = CandidateSnapshot(baseline_sha=_BASELINE, entries=entries)
    second = CandidateSnapshot(baseline_sha=_BASELINE, entries=entries)

    assert first.fingerprint() == second.fingerprint()


def test_fingerprint_changes_with_content() -> None:
    unchanged = CandidateSnapshot(baseline_sha=_BASELINE, entries=(_entry("a.txt", content="1"),))
    changed = CandidateSnapshot(baseline_sha=_BASELINE, entries=(_entry("a.txt", content="2"),))

    assert unchanged.fingerprint() != changed.fingerprint()


def test_fingerprint_changes_with_path() -> None:
    one = CandidateSnapshot(baseline_sha=_BASELINE, entries=(_entry("a.txt"),))
    other = CandidateSnapshot(baseline_sha=_BASELINE, entries=(_entry("b.txt"),))

    assert one.fingerprint() != other.fingerprint()


def test_fingerprint_independent_of_baseline_sha() -> None:
    entries = (_entry("a.txt"),)
    first = CandidateSnapshot(baseline_sha="a" * 40, entries=entries)
    second = CandidateSnapshot(baseline_sha="b" * 40, entries=entries)

    assert first.fingerprint() == second.fingerprint()


def test_candidate_identity_combines_baseline_and_fingerprint() -> None:
    snapshot = CandidateSnapshot(baseline_sha=_BASELINE, entries=(_entry("a.txt"),))

    identity = CandidateIdentity.from_snapshot(snapshot)

    assert identity.baseline_sha == _BASELINE
    assert identity.fingerprint == snapshot.fingerprint()


def test_candidate_identity_differs_when_baseline_differs() -> None:
    entries = (_entry("a.txt"),)
    a = CandidateIdentity.from_snapshot(CandidateSnapshot(baseline_sha="a" * 40, entries=entries))
    b = CandidateIdentity.from_snapshot(CandidateSnapshot(baseline_sha="b" * 40, entries=entries))

    assert a != b
