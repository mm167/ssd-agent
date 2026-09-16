from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import Attempt, Condition, NextAuthorizedAction, Phase


def _attempt(**overrides: object) -> Attempt:
    fields: dict[str, object] = {
        "attempt_id": "a1",
        "task_id": "T002",
        "phase": Phase.READINESS,
        "baseline_sha": "a" * 40,
    }
    fields.update(overrides)
    return Attempt(**fields)  # type: ignore[arg-type]


def test_minimal_valid_attempt() -> None:
    attempt = _attempt()

    assert attempt.phase is Phase.READINESS
    assert attempt.condition is None
    assert attempt.candidate_id is None
    assert attempt.schema_version == 1


def test_requires_baseline_sha() -> None:
    with pytest.raises(ValidationError):
        Attempt(attempt_id="a1", task_id="T002", phase=Phase.READINESS)  # type: ignore[call-arg]


def test_rejects_empty_identity_fields() -> None:
    with pytest.raises(ValidationError):
        _attempt(attempt_id="")

    with pytest.raises(ValidationError):
        _attempt(task_id="")

    with pytest.raises(ValidationError):
        _attempt(baseline_sha="")


def test_rejects_unsupported_phase_value() -> None:
    with pytest.raises(ValidationError):
        _attempt(phase="not-a-real-phase")


def test_rejects_unsupported_condition_value() -> None:
    with pytest.raises(ValidationError):
        _attempt(condition="not-a-real-condition")


def test_condition_and_next_action_are_optional() -> None:
    attempt = _attempt(
        condition=Condition.ENVIRONMENT_BLOCKED,
        next_authorized_action=NextAuthorizedAction(action="RESOLVE_ENVIRONMENT"),
    )

    assert attempt.condition is Condition.ENVIRONMENT_BLOCKED
    assert attempt.next_authorized_action is not None
    assert attempt.next_authorized_action.action == "RESOLVE_ENVIRONMENT"


def test_next_authorized_action_requires_non_empty_action() -> None:
    with pytest.raises(ValidationError):
        NextAuthorizedAction(action="")


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        _attempt(unexpected="value")
