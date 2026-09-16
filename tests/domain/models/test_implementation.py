from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.configuration.models import AgentRole
from sdd_agent.domain.models import (
    EvidenceContext,
    ImplementationCompletionStatus,
    ImplementationReport,
)


def _context_with_candidate() -> EvidenceContext:
    return EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")


def test_implementation_report_minimal() -> None:
    report = ImplementationReport(
        report_id="i1",
        context=_context_with_candidate(),
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=ImplementationCompletionStatus.COMPLETED,
        task_scope_summary="Implemented T002 domain models.",
    )

    assert report.completion_status is ImplementationCompletionStatus.COMPLETED
    assert report.changed_paths == []


def test_implementation_report_requires_candidate_id() -> None:
    with pytest.raises(ValidationError):
        ImplementationReport(
            report_id="i1",
            context=EvidenceContext(task_id="T002", attempt_id="a1"),
            implementation_role=AgentRole.IMPLEMENTER,
            completion_status=ImplementationCompletionStatus.COMPLETED,
            task_scope_summary="x",
        )


def test_implementation_report_rejects_unsupported_completion_status() -> None:
    with pytest.raises(ValidationError):
        ImplementationReport(
            report_id="i1",
            context=_context_with_candidate(),
            implementation_role=AgentRole.IMPLEMENTER,
            completion_status="DONE",
            task_scope_summary="x",
        )


def test_implementation_report_reuses_configuration_agent_role() -> None:
    with pytest.raises(ValidationError):
        ImplementationReport(
            report_id="i1",
            context=_context_with_candidate(),
            implementation_role="not-a-real-role",
            completion_status=ImplementationCompletionStatus.COMPLETED,
            task_scope_summary="x",
        )


def test_implementation_report_requires_task_scope_summary() -> None:
    with pytest.raises(ValidationError):
        ImplementationReport(
            report_id="i1",
            context=_context_with_candidate(),
            implementation_role=AgentRole.IMPLEMENTER,
            completion_status=ImplementationCompletionStatus.COMPLETED,
            task_scope_summary="",
        )


def test_implementation_report_is_frozen() -> None:
    report = ImplementationReport(
        report_id="i1",
        context=_context_with_candidate(),
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=ImplementationCompletionStatus.COMPLETED,
        task_scope_summary="x",
    )

    with pytest.raises(ValidationError):
        report.completion_status = ImplementationCompletionStatus.INCOMPLETE  # type: ignore[misc]


def test_implementation_report_becomes_non_applicable_to_changed_candidate() -> None:
    report_context = _context_with_candidate()
    changed_candidate_context = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c2")

    assert not report_context.applies_to(changed_candidate_context)
