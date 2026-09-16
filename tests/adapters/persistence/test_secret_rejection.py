from __future__ import annotations

from pathlib import Path

import pytest

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models import EvidenceContext, HumanDecision, HumanDecisionType, WorkflowEvent
from sdd_agent.domain.models.attempt import Attempt
from sdd_agent.domain.models.enums import Phase


def _attempt(baseline_sha: str = "0" * 40) -> Attempt:
    return Attempt(attempt_id="a1", task_id="T003", phase=Phase.READINESS, baseline_sha=baseline_sha)


# -- the reviewer's exact demonstrated attack: api_key in an event payload -


def test_event_payload_with_secret_shaped_key_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="CI_OBSERVED",
        payload={"api_key": "sk-live-super-secret"},
    )

    with pytest.raises(PersistenceError):
        store.append_event(event)

    events_path = root / "attempts" / "T003" / "a1" / "events.jsonl"
    assert not events_path.exists()


def test_event_payload_with_credential_bearing_url_value_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="CI_OBSERVED",
        payload={"run_url": "https://x-access-token:ghp_exampleSecret@github.com/org/repo/actions/runs/1"},
    )

    with pytest.raises(PersistenceError):
        store.append_event(event)

    events_path = root / "attempts" / "T003" / "a1" / "events.jsonl"
    assert not events_path.exists()


def test_clean_event_payload_is_accepted(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="CI_OBSERVED",
        payload={"status": "green", "run_id": "42"},
    )

    store.append_event(event)  # must not raise

    assert [e.event_id for e in store.read_events("T003", "a1")] == ["e1"]


# -- current state / attempt record / reports all apply the same guard -----


def test_save_current_rejects_credential_bearing_value_in_any_field(tmp_path: Path) -> None:
    # `Attempt` has `extra="forbid"`, so a stray secret-*named* field cannot
    # even be constructed; this proves value-scanning (not just key-name
    # scanning) also applies to whichever existing field happens to carry a
    # credential-bearing string.
    store = LocalPersistenceStore(tmp_path / ".sdd")
    attempt = _attempt(baseline_sha="https://x-access-token:ghp_exampleSecret@github.com/org/repo.git")

    with pytest.raises(PersistenceError):
        store.save_current(attempt)

    assert store.load_current() is None


def test_save_attempt_record_rejects_secret_bearing_data(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    attempt = _attempt(baseline_sha="https://user:hunter2@example.com/repo.git")

    with pytest.raises(PersistenceError):
        store.save_attempt_record(attempt)

    attempt_path = root / "attempts" / "T003" / "a1" / "attempt.json"
    assert not attempt_path.exists()


def test_append_report_accepts_clean_human_decision(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    decision = HumanDecision(
        decision_id="d1",
        decision_type=HumanDecisionType.COMMIT_APPROVAL,
        context=EvidenceContext(task_id="T003", attempt_id="a1", candidate_id="c1"),
        choice="approve",
    )

    store.append_report("T003", "a1", "decisions", "d1", decision)  # must not raise

    assert store.load_report("T003", "a1", "decisions", "d1", HumanDecision) == decision


def test_append_report_rejects_secret_shaped_key_via_generic_evidence(tmp_path: Path) -> None:
    from pydantic import BaseModel, ConfigDict

    class _GenericEvidence(BaseModel):
        model_config = ConfigDict(extra="forbid")

        note: str
        details: dict[str, str]

    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    evidence = _GenericEvidence(note="ci run", details={"github_token": "ghp_exampleSecret"})

    with pytest.raises(PersistenceError):
        store.append_report("T003", "a1", "evidence", "ev1", evidence)

    evidence_path = root / "attempts" / "T003" / "a1" / "evidence" / "ev1.json"
    assert not evidence_path.exists()


def test_no_temp_file_left_behind_after_secret_rejection(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    event = WorkflowEvent(
        event_id="e1", task_id="T003", attempt_id="a1", event_type="CI_OBSERVED", payload={"password": "hunter2"}
    )

    with pytest.raises(PersistenceError):
        store.append_event(event)

    # No bytes -- not even a temp/partial file -- were written for the
    # rejected data; the guard runs before filesystem mutation.
    assert list(root.rglob("*")) == [] or not root.exists()
