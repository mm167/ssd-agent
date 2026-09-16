from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import (
    EvidenceContext,
    ValidationObligation,
    ValidationResult,
    ValidationStatus,
    ValidationWaiver,
    WaiverEligibleCause,
)


def _context_with_candidate(**overrides: object) -> EvidenceContext:
    fields: dict[str, object] = {"task_id": "T002", "attempt_id": "a1", "candidate_id": "c1"}
    fields.update(overrides)
    return EvidenceContext(**fields)  # type: ignore[arg-type]


def test_validation_obligation_minimal() -> None:
    obligation = ValidationObligation(
        obligation_id="pytest",
        description="Run the pytest suite",
        execution_reference="uv run pytest",
        required=True,
    )

    assert obligation.non_waivable is False


def test_validation_obligation_requires_non_empty_fields() -> None:
    with pytest.raises(ValidationError):
        ValidationObligation(
            obligation_id="",
            description="x",
            execution_reference="x",
            required=True,
        )


@pytest.mark.parametrize("status", [ValidationStatus.PASSED, ValidationStatus.FAILED, ValidationStatus.NOT_RUN])
def test_validation_result_accepts_each_status(status: ValidationStatus) -> None:
    result = ValidationResult(
        result_id="v1",
        obligation_id="pytest",
        context=_context_with_candidate(),
        status=status,
    )

    assert result.status is status


def test_validation_result_rejects_unsupported_status() -> None:
    with pytest.raises(ValidationError):
        ValidationResult(
            result_id="v1",
            obligation_id="pytest",
            context=_context_with_candidate(),
            status="SUCCESS",
        )


def test_validation_result_requires_candidate_id() -> None:
    with pytest.raises(ValidationError):
        ValidationResult(
            result_id="v1",
            obligation_id="pytest",
            context=EvidenceContext(task_id="T002", attempt_id="a1"),
            status=ValidationStatus.PASSED,
        )


def test_validation_result_is_frozen() -> None:
    result = ValidationResult(
        result_id="v1",
        obligation_id="pytest",
        context=_context_with_candidate(),
        status=ValidationStatus.PASSED,
    )

    with pytest.raises(ValidationError):
        result.status = ValidationStatus.FAILED  # type: ignore[misc]


def test_validation_waiver_requires_environment_cause() -> None:
    with pytest.raises(ValidationError):
        ValidationWaiver(
            waiver_id="w1",
            obligation_id="pytest",
            context=_context_with_candidate(),
            cause="convenience",
            validation_result_id="v1",
            human_decision_id="d1",
            reason="skip",
        )


def test_validation_waiver_valid() -> None:
    waiver = ValidationWaiver(
        waiver_id="w1",
        obligation_id="pytest",
        context=_context_with_candidate(),
        cause=WaiverEligibleCause.ENVIRONMENT,
        validation_result_id="v1",
        human_decision_id="d1",
        reason="CI runner network outage",
    )

    assert waiver.cause is WaiverEligibleCause.ENVIRONMENT


def test_validation_waiver_requires_candidate_id() -> None:
    with pytest.raises(ValidationError):
        ValidationWaiver(
            waiver_id="w1",
            obligation_id="pytest",
            context=EvidenceContext(task_id="T002", attempt_id="a1"),
            cause=WaiverEligibleCause.ENVIRONMENT,
            validation_result_id="v1",
            human_decision_id="d1",
            reason="skip",
        )
