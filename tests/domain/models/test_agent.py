from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from sdd_agent.configuration.models import AgentProvider, AgentRole
from sdd_agent.domain.models import (
    AgentExecutionStatus,
    AgentReportType,
    AgentRequest,
    AgentResult,
    EvidenceContext,
    ImplementationCompletionStatus,
    ImplementationReport,
    ReadinessReport,
    build_successful_agent_result,
)


def _context(candidate_id: str = "cand-1") -> EvidenceContext:
    return EvidenceContext(task_id="T007", attempt_id="attempt-1", candidate_id=candidate_id)


def _request(
    *,
    role: AgentRole = AgentRole.IMPLEMENTER,
    provider: AgentProvider = AgentProvider.CODEX,
    expected_report_type: AgentReportType = AgentReportType.IMPLEMENTATION_REPORT,
    context: EvidenceContext | None = None,
) -> AgentRequest:
    context = context or _context()
    return AgentRequest(
        request_id="req-1",
        role=role,
        provider=provider,
        repository=Path("."),
        task_id=context.task_id,
        attempt_id=context.attempt_id,
        context=context,
        instructions="Implement the active task.",
        expected_report_type=expected_report_type,
    )


def _implementation_report(
    *,
    context: EvidenceContext | None = None,
    role: AgentRole = AgentRole.IMPLEMENTER,
    status: ImplementationCompletionStatus = ImplementationCompletionStatus.COMPLETED,
) -> ImplementationReport:
    return ImplementationReport(
        report_id="impl-1",
        context=context or _context(),
        implementation_role=role,
        completion_status=status,
        task_scope_summary="Implemented the T007 contract.",
    )


def test_agent_request_binds_role_provider_and_context_without_equating_them() -> None:
    request = _request(role=AgentRole.IMPLEMENTER, provider=AgentProvider.CODEX)

    assert request.role is AgentRole.IMPLEMENTER
    assert request.provider is AgentProvider.CODEX
    assert AgentRole.IMPLEMENTER.value != AgentProvider.CODEX.value


def test_agent_request_allows_different_provider_assignment_for_same_role() -> None:
    codex_request = _request(provider=AgentProvider.CODEX)
    claude_request = _request(provider=AgentProvider.CLAUDE_CODE)

    assert codex_request.role is claude_request.role is AgentRole.IMPLEMENTER
    assert codex_request.provider is AgentProvider.CODEX
    assert claude_request.provider is AgentProvider.CLAUDE_CODE


def test_agent_request_rejects_context_identity_mismatch() -> None:
    with pytest.raises(ValidationError):
        AgentRequest(
            request_id="req-1",
            role=AgentRole.IMPLEMENTER,
            provider=AgentProvider.FAKE,
            repository=Path("."),
            task_id="T007",
            attempt_id="attempt-1",
            context=EvidenceContext(task_id="T999", attempt_id="attempt-1", candidate_id="cand-1"),
            instructions="x",
            expected_report_type=AgentReportType.IMPLEMENTATION_REPORT,
        )


def test_successful_agent_result_requires_structured_report() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            execution_id="exec-1",
            request_id="req-1",
            role=AgentRole.IMPLEMENTER,
            provider=AgentProvider.FAKE,
            context=_context(),
            execution_status=AgentExecutionStatus.SUCCEEDED,
            report_type=AgentReportType.IMPLEMENTATION_REPORT,
        )


def test_successful_agent_result_accepts_matching_implementation_role() -> None:
    result = AgentResult(
        execution_id="exec-1",
        request_id="req-1",
        role=AgentRole.IMPLEMENTER,
        provider=AgentProvider.FAKE,
        context=_context(),
        execution_status=AgentExecutionStatus.SUCCEEDED,
        report_type=AgentReportType.IMPLEMENTATION_REPORT,
        structured_report=_implementation_report(role=AgentRole.IMPLEMENTER),
    )

    assert result.structured_report is not None


def test_failed_agent_result_cannot_carry_successful_report_evidence() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            execution_id="exec-1",
            request_id="req-1",
            role=AgentRole.IMPLEMENTER,
            provider=AgentProvider.FAKE,
            context=_context(),
            execution_status=AgentExecutionStatus.FAILED,
            report_type=AgentReportType.IMPLEMENTATION_REPORT,
            structured_report=_implementation_report(),
        )


def test_successful_agent_result_rejects_report_for_different_candidate() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            execution_id="exec-1",
            request_id="req-1",
            role=AgentRole.IMPLEMENTER,
            provider=AgentProvider.FAKE,
            context=_context("cand-2"),
            execution_status=AgentExecutionStatus.SUCCEEDED,
            report_type=AgentReportType.IMPLEMENTATION_REPORT,
            structured_report=_implementation_report(context=_context("cand-1")),
        )


def test_successful_agent_result_rejects_report_type_mismatch() -> None:
    readiness = ReadinessReport(
        report_id="ready-1",
        context=EvidenceContext(task_id="T007", attempt_id="attempt-1"),
        ready_for_code=True,
        rationale="ready",
    )

    with pytest.raises(ValidationError):
        AgentResult(
            execution_id="exec-1",
            request_id="req-1",
            role=AgentRole.READINESS,
            provider=AgentProvider.FAKE,
            context=EvidenceContext(task_id="T007", attempt_id="attempt-1"),
            execution_status=AgentExecutionStatus.SUCCEEDED,
            report_type=AgentReportType.IMPLEMENTATION_REPORT,
            structured_report=readiness,
        )


def test_successful_agent_result_rejects_implementation_report_for_different_role() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            execution_id="exec-1",
            request_id="req-1",
            role=AgentRole.REVIEWER,
            provider=AgentProvider.FAKE,
            context=_context(),
            execution_status=AgentExecutionStatus.SUCCEEDED,
            report_type=AgentReportType.IMPLEMENTATION_REPORT,
            structured_report=_implementation_report(role=AgentRole.IMPLEMENTER),
        )


def test_report_validation_hook_requires_expected_report_type() -> None:
    request = _request(expected_report_type=AgentReportType.REVIEW_REPORT)

    with pytest.raises(ValueError):
        build_successful_agent_result(
            request=request,
            execution_id="exec-1",
            structured_report=_implementation_report(),
        )


def test_report_validation_hook_requires_implementation_role_to_match_request_role() -> None:
    request = _request(role=AgentRole.REVIEWER)

    with pytest.raises(ValueError):
        build_successful_agent_result(
            request=request,
            execution_id="exec-1",
            structured_report=_implementation_report(role=AgentRole.IMPLEMENTER),
        )


def test_report_validation_hook_binds_successful_result_to_request() -> None:
    request = _request(provider=AgentProvider.FAKE)
    result = build_successful_agent_result(
        request=request,
        execution_id="exec-1",
        structured_report=_implementation_report(),
        session_reference="fake-session-1",
    )

    assert result.execution_status is AgentExecutionStatus.SUCCEEDED
    assert result.role is AgentRole.IMPLEMENTER
    assert result.provider is AgentProvider.FAKE
    assert result.report_type is AgentReportType.IMPLEMENTATION_REPORT
    assert isinstance(result.structured_report, ImplementationReport)
