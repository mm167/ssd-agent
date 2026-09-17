from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.diagnostics.errors import PersistenceError
from sdd_agent.domain.models import EvidenceContext, HumanDecision, HumanDecisionType, WorkflowEvent
from sdd_agent.domain.models.attempt import Attempt, NextAuthorizedAction
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


@pytest.mark.parametrize(
    "credential_text",
    [
        "provider returned ghp_SYNTHETICCredentialValue",
        "provider returned github_pat_SYNTHETICCredentialValue",
        "provider returned sk-ant-syntheticCredentialValue",
        "provider returned sk-proj-syntheticCredentialValue",
        "provider returned AKIA1234567890ABCDEF",
    ],
)
def test_event_payload_with_bare_credential_in_free_text_is_rejected(
    tmp_path: Path,
    credential_text: str,
) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="AGENT_OUTPUT_CAPTURED",
        payload={
            "agent_stdout": credential_text,
            "details": {"message": "otherwise harmless nested payload"},
        },
    )

    with pytest.raises(PersistenceError) as excinfo:
        store.append_event(event)

    assert "payload.agent_stdout" in excinfo.value.details["offending_values"]
    assert "SYNTHETICCredentialValue" not in str(excinfo.value)
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


def test_event_payload_with_legitimate_identifiers_in_free_text_is_accepted(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="DIAGNOSTICS_CAPTURED",
        payload={
            "agent_stdout": "ordinary diagnostic text",
            "details": {
                "commit": "0123456789abcdef0123456789abcdef01234567",
                "fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "session_reference": "fake-session-2026-09-17",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "report_id": "readiness-report-2026-09-17-001",
            },
        },
    )

    store.append_event(event)

    assert [e.payload for e in store.read_events("T003", "a1")] == [event.payload]


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


def test_save_current_rejects_bare_credential_in_free_text_field(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    attempt = Attempt(
        attempt_id="a1",
        task_id="T003",
        phase=Phase.READINESS,
        baseline_sha="0" * 40,
        next_authorized_action=NextAuthorizedAction(
            action="BLOCKED",
            reason="provider returned sk-ant-syntheticCredentialValue",
        ),
    )

    with pytest.raises(PersistenceError) as excinfo:
        store.save_current(attempt)

    assert "next_authorized_action.reason" in excinfo.value.details["offending_values"]
    assert store.load_current() is None


def test_save_attempt_record_rejects_secret_bearing_data(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    attempt = _attempt(baseline_sha="https://user:hunter2@example.com/repo.git")

    with pytest.raises(PersistenceError):
        store.save_attempt_record(attempt)

    attempt_path = root / "attempts" / "T003" / "a1" / "attempt.json"
    assert not attempt_path.exists()


def test_save_attempt_record_rejects_bare_credential_in_free_text_field(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    attempt = Attempt(
        attempt_id="a1",
        task_id="T003",
        phase=Phase.READINESS,
        baseline_sha="0" * 40,
        next_authorized_action=NextAuthorizedAction(
            action="BLOCKED",
            reason="provider returned ghp_SYNTHETICCredentialValue",
        ),
    )

    with pytest.raises(PersistenceError) as excinfo:
        store.save_attempt_record(attempt)

    assert "next_authorized_action.reason" in excinfo.value.details["offending_values"]
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


def test_append_report_rejects_bare_credential_in_nested_free_text(tmp_path: Path) -> None:
    class _GenericEvidence(BaseModel):
        model_config = ConfigDict(extra="forbid")

        agent_stdout: str
        details: dict[str, object]

    root = tmp_path / ".sdd"
    store = LocalPersistenceStore(root)
    evidence = _GenericEvidence(
        agent_stdout="provider returned AKIA1234567890ABCDEF",
        details={"message": "otherwise harmless report payload"},
    )

    with pytest.raises(PersistenceError) as excinfo:
        store.append_report("T003", "a1", "evidence", "ev1", evidence)

    assert "agent_stdout" in excinfo.value.details["offending_values"]
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
