from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import Condition, EvidenceContext, ReadinessReport


def _context(**overrides: object) -> EvidenceContext:
    fields: dict[str, object] = {"task_id": "T002", "attempt_id": "a1"}
    fields.update(overrides)
    return EvidenceContext(**fields)  # type: ignore[arg-type]


def test_ready_report_without_condition() -> None:
    report = ReadinessReport(
        report_id="r1",
        context=_context(),
        ready_for_code=True,
        rationale="T001 CLOSED; contract unambiguous.",
    )

    assert report.ready_for_code is True
    assert report.condition is None


def test_not_ready_report_requires_condition() -> None:
    with pytest.raises(ValidationError):
        ReadinessReport(
            report_id="r1",
            context=_context(),
            ready_for_code=False,
            rationale="Dependency unsatisfied.",
        )


def test_ready_report_rejects_condition_present() -> None:
    with pytest.raises(ValidationError):
        ReadinessReport(
            report_id="r1",
            context=_context(),
            ready_for_code=True,
            condition=Condition.TASKS_REQUIRED,
            rationale="Contradiction.",
        )


def test_not_ready_report_with_condition_is_valid() -> None:
    report = ReadinessReport(
        report_id="r1",
        context=_context(),
        ready_for_code=False,
        condition=Condition.TASK_DEPENDENCY_UNSATISFIED,
        rationale="T001 is not yet CLOSED.",
    )

    assert report.condition is Condition.TASK_DEPENDENCY_UNSATISFIED


def test_rejects_missing_rationale() -> None:
    with pytest.raises(ValidationError):
        ReadinessReport(
            report_id="r1",
            context=_context(),
            ready_for_code=True,
        )


def test_is_frozen() -> None:
    report = ReadinessReport(
        report_id="r1",
        context=_context(),
        ready_for_code=True,
        rationale="ok",
    )

    with pytest.raises(ValidationError):
        report.ready_for_code = False  # type: ignore[misc]


def test_rejects_missing_context() -> None:
    with pytest.raises(ValidationError):
        ReadinessReport(report_id="r1", ready_for_code=True, rationale="ok")  # type: ignore[call-arg]
