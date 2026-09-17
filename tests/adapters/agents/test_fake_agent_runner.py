from __future__ import annotations

from pathlib import Path

import pytest

from sdd_agent.adapters.agents import FakeAgentOutcome, FakeAgentRunner
from sdd_agent.configuration.models import AgentProvider, AgentRole
from sdd_agent.domain.models import (
    AgentExecutionStatus,
    AgentReportType,
    AgentRequest,
    EvidenceContext,
    ImplementationCompletionStatus,
    ImplementationReport,
)


def _context(candidate_id: str = "cand-1") -> EvidenceContext:
    return EvidenceContext(task_id="T007", attempt_id="attempt-1", candidate_id=candidate_id)


def _request(request_id: str = "req-1", provider: AgentProvider = AgentProvider.FAKE) -> AgentRequest:
    context = _context()
    return AgentRequest(
        request_id=request_id,
        role=AgentRole.IMPLEMENTER,
        provider=provider,
        repository=Path("."),
        task_id=context.task_id,
        attempt_id=context.attempt_id,
        context=context,
        instructions="Implement T007.",
        expected_report_type=AgentReportType.IMPLEMENTATION_REPORT,
    )


def _report() -> ImplementationReport:
    return ImplementationReport(
        report_id="impl-1",
        context=_context(),
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=ImplementationCompletionStatus.COMPLETED,
        task_scope_summary="Implemented T007.",
    )


def test_fake_agent_runner_returns_scripted_success() -> None:
    runner = FakeAgentRunner({"req-1": FakeAgentOutcome.success(execution_id="exec-1", structured_report=_report())})

    result = runner.run(_request())

    assert result.execution_status is AgentExecutionStatus.SUCCEEDED
    assert result.execution_id == "exec-1"
    assert result.request_id == "req-1"
    assert runner.calls == [_request()]


def test_fake_agent_runner_returns_scripted_timeout_without_report_evidence() -> None:
    runner = FakeAgentRunner(
        {
            "req-1": FakeAgentOutcome.failure(
                status=AgentExecutionStatus.TIMEOUT,
                execution_id="exec-1",
                diagnostics=("agent timed out",),
            )
        }
    )

    result = runner.run(_request())

    assert result.execution_status is AgentExecutionStatus.TIMEOUT
    assert result.structured_report is None
    assert result.diagnostics == ("agent timed out",)


def test_fake_agent_runner_malformed_output_is_not_successful_evidence() -> None:
    runner = FakeAgentRunner({"req-1": FakeAgentOutcome.malformed(execution_id="exec-1")})

    result = runner.run(_request())

    assert result.execution_status is AgentExecutionStatus.MALFORMED_OUTPUT
    assert result.structured_report is None
    assert result.report_type is None


def test_fake_agent_runner_unscripted_request_raises_rather_than_guessing() -> None:
    runner = FakeAgentRunner({})

    with pytest.raises(KeyError):
        runner.run(_request("missing"))


def test_fake_agent_runner_validates_scripted_report_context() -> None:
    stale_report = ImplementationReport(
        report_id="impl-stale",
        context=_context("stale-candidate"),
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=ImplementationCompletionStatus.COMPLETED,
        task_scope_summary="Stale evidence.",
    )
    runner = FakeAgentRunner({"req-1": FakeAgentOutcome.success(execution_id="exec-1", structured_report=stale_report)})

    with pytest.raises(ValueError):
        runner.run(_request())


def test_fake_runner_is_not_a_concrete_production_provider_substitute() -> None:
    request = _request(provider=AgentProvider.FAKE)
    runner = FakeAgentRunner({"req-1": FakeAgentOutcome.success(execution_id="exec-1", structured_report=_report())})

    result = runner.run(request)

    assert result.provider is AgentProvider.FAKE
    assert result.provider is not AgentProvider.CODEX
    assert result.provider is not AgentProvider.CLAUDE_CODE
