from __future__ import annotations

from pathlib import Path

from sdd_agent.adapters.persistence.local_store import LocalPersistenceStore
from sdd_agent.adapters.persistence.recovery import load_recovered_state
from sdd_agent.domain.models import Phase, WorkflowEvent
from sdd_agent.domain.models.attempt import Attempt


def _attempt(*, task_id: str = "T003", attempt_id: str = "a1", phase: Phase = Phase.VALIDATION) -> Attempt:
    return Attempt(attempt_id=attempt_id, task_id=task_id, phase=phase, baseline_sha="0" * 40)


def test_recovery_returns_none_when_no_current_attempt(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")

    assert load_recovered_state(store, "T003") is None


def test_recovery_returns_none_for_a_different_task(tmp_path: Path) -> None:
    store = LocalPersistenceStore(tmp_path / ".sdd")
    store.save_current(_attempt(task_id="T003"))

    assert load_recovered_state(store, "T004") is None


def test_recovery_reconstructs_attempt_and_events_from_a_fresh_process(tmp_path: Path) -> None:
    root = tmp_path / ".sdd"

    # Simulate the process that ran the Attempt, before it exits/crashes.
    writer = LocalPersistenceStore(root)
    attempt = _attempt()
    writer.save_current(attempt)
    writer.append_event(
        WorkflowEvent(event_id="e1", task_id="T003", attempt_id="a1", event_type="ATTEMPT_STARTED")
    )
    writer.append_event(
        WorkflowEvent(event_id="e2", task_id="T003", attempt_id="a1", event_type="READINESS_COMPLETED")
    )
    del writer  # nothing about recovery may depend on this object still existing

    # A brand new process/object, constructed only from the root path, with
    # no reference to `writer` and no conversational context.
    reader = LocalPersistenceStore(root)
    recovered = load_recovered_state(reader, "T003")

    assert recovered is not None
    assert recovered.attempt == attempt
    assert [event.event_id for event in recovered.events] == ["e1", "e2"]
