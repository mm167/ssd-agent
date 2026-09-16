from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import CURRENT_SCHEMA_VERSION, WorkflowEvent


def test_workflow_event_minimal() -> None:
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="ATTEMPT_STARTED",
    )

    assert event.event_type == "ATTEMPT_STARTED"
    assert event.schema_version == CURRENT_SCHEMA_VERSION
    assert event.payload == {}
    assert event.candidate_id is None


def test_rejects_empty_event_type() -> None:
    with pytest.raises(ValidationError):
        WorkflowEvent(event_id="e1", task_id="T003", attempt_id="a1", event_type="")


def test_requires_task_and_attempt_id() -> None:
    with pytest.raises(ValidationError):
        WorkflowEvent(event_id="e1", attempt_id="a1", event_type="ATTEMPT_STARTED")  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        WorkflowEvent(event_id="e1", task_id="T003", event_type="ATTEMPT_STARTED")  # type: ignore[call-arg]


def test_is_frozen() -> None:
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="ATTEMPT_STARTED",
    )

    with pytest.raises(ValidationError):
        event.event_type = "OTHER"  # type: ignore[misc]


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        WorkflowEvent(
            event_id="e1",
            task_id="T003",
            attempt_id="a1",
            event_type="ATTEMPT_STARTED",
            unexpected="value",
        )


def test_carries_optional_candidate_id_and_payload() -> None:
    event = WorkflowEvent(
        event_id="e1",
        task_id="T003",
        attempt_id="a1",
        event_type="VALIDATION_COMPLETED",
        candidate_id="c1",
        payload={"status": "passed"},
    )

    assert event.candidate_id == "c1"
    assert event.payload == {"status": "passed"}
