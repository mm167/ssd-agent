from __future__ import annotations

from pathlib import Path

import pytest

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models import EvidenceContext, ReadinessReport, WorkflowEvent
from sdd_agent.domain.models.attempt import Attempt
from sdd_agent.domain.models.enums import Phase

_MALICIOUS_COMPONENTS = [
    "../escaped",
    "../../escaped",
    "..\\escaped",
    "..\\..\\escaped",
    "/etc/passwd",
    "\\\\server\\share",
    "C:\\Windows\\System32",
    "..",
    ".",
]


def _attempt(task_id: str = "T003", attempt_id: str = "a1") -> Attempt:
    return Attempt(attempt_id=attempt_id, task_id=task_id, phase=Phase.READINESS, baseline_sha="0" * 40)


def _readiness_report(task_id: str = "T003", attempt_id: str = "a1", report_id: str = "r1") -> ReadinessReport:
    return ReadinessReport(
        report_id=report_id,
        context=EvidenceContext(task_id=task_id, attempt_id=attempt_id),
        ready_for_code=True,
        rationale="ok",
    )


# -- malicious task_id / attempt_id across every entry point --------------


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_save_attempt_record_rejects_malicious_task_id(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.save_attempt_record(_attempt(task_id=malicious))


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_save_attempt_record_rejects_malicious_attempt_id(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.save_attempt_record(_attempt(attempt_id=malicious))


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_load_attempt_record_rejects_malicious_identifiers(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.load_attempt_record(malicious, "a1")

    with pytest.raises(PersistenceError):
        store.load_attempt_record("T003", malicious)


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_append_event_rejects_malicious_identifiers(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.append_event(
            WorkflowEvent(event_id="e1", task_id=malicious, attempt_id="a1", event_type="ATTEMPT_STARTED")
        )


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_read_events_rejects_malicious_identifiers(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.read_events(malicious, "a1")


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_append_report_rejects_malicious_category(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.append_report("T003", "a1", malicious, "r1", _readiness_report())


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_append_report_rejects_malicious_report_id(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.append_report("T003", "a1", "readiness", malicious, _readiness_report(report_id=malicious))


@pytest.mark.parametrize("malicious", _MALICIOUS_COMPONENTS)
def test_list_report_ids_rejects_malicious_category(tmp_path: Path, malicious: str) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.list_report_ids("T003", "a1", malicious)


def test_empty_identifier_is_rejected(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.list_report_ids("T003", "a1", "")


# -- demonstrate no filesystem escape actually occurs ----------------------


def test_malicious_task_id_produces_no_write_outside_sdd_root(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)

    with pytest.raises(PersistenceError):
        store.save_attempt_record(_attempt(task_id="../../escaped"))

    # Rejection happens before any directory or file is created at all, so
    # nothing may exist anywhere under the test's isolated temp directory --
    # neither the intended `.sdd/` layout nor any escaped location the
    # `../../escaped` component would otherwise have resolved to.
    assert list(tmp_path.rglob("*")) == []


def test_malicious_report_id_produces_no_write_outside_sdd_root(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)

    with pytest.raises(PersistenceError):
        store.append_report("T003", "a1", "readiness", "../../../escaped", _readiness_report())

    assert list(tmp_path.rglob("*")) == []


def test_ensure_within_root_rejects_a_path_that_escapes_even_without_separators(tmp_path: Path) -> None:
    """Defense-in-depth: even if a path were constructed outside the normal
    `_attempt_dir`/`_category_dir`/`_report_path` builders, the root-containment
    check independently refuses to operate on it.
    """
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    outside_path = tmp_path.parent / "definitely-outside" / "file.json"

    with pytest.raises(PersistenceError):
        store._ensure_within_root(outside_path)  # noqa: SLF001 -- exercising the safety net directly


# -- legitimate identifiers keep working -----------------------------------


def test_legitimate_identifiers_with_dots_hyphens_underscores_round_trip(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    attempt = _attempt(task_id="T003", attempt_id="attempt-001")
    report = _readiness_report(task_id="T003", attempt_id="attempt-001", report_id="r.1_final")

    store.save_attempt_record(attempt)
    store.append_report("T003", "attempt-001", "readiness", "r.1_final", report)
    store.append_event(
        WorkflowEvent(event_id="e1", task_id="T003", attempt_id="attempt-001", event_type="ATTEMPT_STARTED")
    )

    assert store.load_attempt_record("T003", "attempt-001") == attempt
    assert store.load_report("T003", "attempt-001", "readiness", "r.1_final", ReadinessReport) == report
    assert [event.event_id for event in store.read_events("T003", "attempt-001")] == ["e1"]


def test_valid_task_and_attempt_isolation_is_preserved(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    store.save_attempt_record(_attempt(task_id="T003", attempt_id="a1"))
    store.save_attempt_record(_attempt(task_id="T004", attempt_id="a1"))

    assert store.load_attempt_record("T003", "a1") is not None
    assert store.load_attempt_record("T004", "a1") is not None
    assert store.load_attempt_record("T003", "a2") is None
