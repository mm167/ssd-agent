from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models import (
    Condition,
    EvidenceContext,
    HumanDecision,
    HumanDecisionType,
    Phase,
    ReadinessReport,
)
from sdd_agent.domain.models.attempt import Attempt


def _attempt(*, task_id: str = "T003", attempt_id: str = "a1", phase: Phase = Phase.READINESS) -> Attempt:
    return Attempt(
        attempt_id=attempt_id,
        task_id=task_id,
        phase=phase,
        baseline_sha="0" * 40,
    )


def _readiness_report(*, report_id: str = "r1", task_id: str = "T003", attempt_id: str = "a1") -> ReadinessReport:
    return ReadinessReport(
        report_id=report_id,
        context=EvidenceContext(task_id=task_id, attempt_id=attempt_id),
        ready_for_code=True,
        rationale="All dependencies satisfied.",
    )


def _human_decision(*, decision_id: str = "d1", task_id: str = "T003", attempt_id: str = "a1") -> HumanDecision:
    return HumanDecision(
        decision_id=decision_id,
        decision_type=HumanDecisionType.COMMIT_APPROVAL,
        context=EvidenceContext(task_id=task_id, attempt_id=attempt_id, candidate_id="c1"),
        choice="approve",
    )


# -- current pointer (mutable) -------------------------------------------


def test_save_and_load_current_round_trip(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    attempt = _attempt()

    store.save_current(attempt)
    loaded = store.load_current()

    assert loaded == attempt


def test_load_current_returns_none_when_missing(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    assert store.load_current() is None


def test_current_pointer_is_overwritable(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    store.save_current(_attempt(phase=Phase.READINESS))

    store.save_current(_attempt(phase=Phase.IMPLEMENTATION))
    loaded = store.load_current()

    assert loaded is not None
    assert loaded.phase is Phase.IMPLEMENTATION


def test_no_leftover_temp_files_after_atomic_write(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)

    store.save_current(_attempt())

    leftovers = list(root.glob("*.tmp"))
    assert leftovers == []


# -- attempt record (append-only) ----------------------------------------


def test_save_and_load_attempt_record_round_trip(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    attempt = _attempt()

    store.save_attempt_record(attempt)
    loaded = store.load_attempt_record(attempt.task_id, attempt.attempt_id)

    assert loaded == attempt


def test_load_attempt_record_returns_none_when_missing(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    assert store.load_attempt_record("T003", "a1") is None


def test_attempt_record_refuses_overwrite(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    attempt = _attempt()
    store.save_attempt_record(attempt)

    with pytest.raises(PersistenceError):
        store.save_attempt_record(_attempt(phase=Phase.IMPLEMENTATION))

    # The original historical record must remain unchanged.
    reloaded = store.load_attempt_record(attempt.task_id, attempt.attempt_id)
    assert reloaded == attempt


# -- reports (append-only) ------------------------------------------------


def test_append_and_load_report_round_trip(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    report = _readiness_report()

    store.append_report("T003", "a1", "readiness", report.report_id, report)
    loaded = store.load_report("T003", "a1", "readiness", report.report_id, ReadinessReport)

    assert loaded == report


def test_append_report_refuses_overwrite_existing_id(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    first = _readiness_report(report_id="r1")
    store.append_report("T003", "a1", "readiness", "r1", first)

    conflicting = ReadinessReport(
        report_id="r1",
        context=EvidenceContext(task_id="T003", attempt_id="a1"),
        ready_for_code=False,
        condition=Condition.TASKS_REQUIRED,
        rationale="Different outcome for the same id.",
    )

    with pytest.raises(PersistenceError):
        store.append_report("T003", "a1", "readiness", "r1", conflicting)

    # Historical evidence must not be mutated by the failed overwrite attempt.
    reloaded = store.load_report("T003", "a1", "readiness", "r1", ReadinessReport)
    assert reloaded == first


def test_load_report_missing_raises_persistence_error(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    with pytest.raises(PersistenceError):
        store.load_report("T003", "a1", "readiness", "missing", ReadinessReport)


def test_list_report_ids_is_sorted_and_empty_when_missing(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    assert store.list_report_ids("T003", "a1", "readiness") == []

    store.append_report("T003", "a1", "readiness", "r2", _readiness_report(report_id="r2"))
    store.append_report("T003", "a1", "readiness", "r1", _readiness_report(report_id="r1"))

    assert store.list_report_ids("T003", "a1", "readiness") == ["r1", "r2"]


def test_load_reports_returns_all_in_category(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    store.append_report("T003", "a1", "decisions", "d1", _human_decision(decision_id="d1"))
    store.append_report("T003", "a1", "decisions", "d2", _human_decision(decision_id="d2"))

    loaded = store.load_reports("T003", "a1", "decisions", HumanDecision)

    assert [decision.decision_id for decision in loaded] == ["d1", "d2"]


def test_categories_are_isolated_between_attempts(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    store.append_report("T003", "a1", "readiness", "r1", _readiness_report(attempt_id="a1"))

    assert store.list_report_ids("T003", "a2", "readiness") == []
    assert store.list_report_ids("T004", "a1", "readiness") == []


# -- corruption / schema-version detection --------------------------------


def test_corrupt_json_raises_persistence_error(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    path = root / "current.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(PersistenceError):
        store.load_current()


def test_schema_version_mismatch_raises_persistence_error(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    path = root / "current.json"
    path.parent.mkdir(parents=True)
    data = _attempt().model_dump(mode="json")
    data["schema_version"] = 999
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(PersistenceError):
        store.load_current()


def test_invalid_model_data_raises_persistence_error(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    path = root / "current.json"
    path.parent.mkdir(parents=True)
    data = _attempt().model_dump(mode="json")
    del data["baseline_sha"]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(PersistenceError):
        store.load_current()


def test_does_not_silently_default_missing_critical_fields(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    path = root / "current.json"
    path.parent.mkdir(parents=True)
    data = _attempt().model_dump(mode="json")
    del data["phase"]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(PersistenceError):
        store.load_current()
