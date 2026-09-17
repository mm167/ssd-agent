"""Deterministic `AgentRunner` test double (TASKS T007; PLAN Section 97)."""

from __future__ import annotations

from collections.abc import Mapping

from sdd_agent.domain.models.agent import (
    AgentExecutionStatus,
    AgentRequest,
    AgentResult,
    AgentStructuredReport,
    build_successful_agent_result,
)
from sdd_agent.ports.agents import AgentRunner


class FakeAgentOutcome:
    """One scripted fake-agent outcome.

    Use `success` for validated structured-report evidence and `failure` for
    deterministic non-success execution facts. `malformed` is a convenience
    for the common T007 adversarial case: provider output could not be
    validated as the required structured report, so no successful evidence is
    produced.
    """

    def __init__(
        self,
        *,
        status: AgentExecutionStatus,
        execution_id: str,
        structured_report: AgentStructuredReport | None = None,
        session_reference: str | None = None,
        diagnostics: tuple[str, ...] = (),
    ) -> None:
        self.status = status
        self.execution_id = execution_id
        self.structured_report = structured_report
        self.session_reference = session_reference
        self.diagnostics = diagnostics

    @classmethod
    def success(
        cls,
        *,
        execution_id: str,
        structured_report: AgentStructuredReport,
        session_reference: str | None = None,
        diagnostics: tuple[str, ...] = (),
    ) -> "FakeAgentOutcome":
        return cls(
            status=AgentExecutionStatus.SUCCEEDED,
            execution_id=execution_id,
            structured_report=structured_report,
            session_reference=session_reference,
            diagnostics=diagnostics,
        )

    @classmethod
    def failure(
        cls,
        *,
        status: AgentExecutionStatus,
        execution_id: str,
        diagnostics: tuple[str, ...] = (),
        session_reference: str | None = None,
    ) -> "FakeAgentOutcome":
        if status is AgentExecutionStatus.SUCCEEDED:
            raise ValueError("FakeAgentOutcome.failure requires a non-success status")
        return cls(
            status=status,
            execution_id=execution_id,
            diagnostics=diagnostics,
            session_reference=session_reference,
        )

    @classmethod
    def malformed(
        cls,
        *,
        execution_id: str,
        diagnostics: tuple[str, ...] = ("malformed structured agent output",),
    ) -> "FakeAgentOutcome":
        return cls.failure(
            status=AgentExecutionStatus.MALFORMED_OUTPUT,
            execution_id=execution_id,
            diagnostics=diagnostics,
        )


class FakeAgentRunner(AgentRunner):
    """Scripted `AgentRunner`: one outcome per `request_id`.

    An unscripted request raises immediately so tests cannot accidentally
    depend on a default successful agent response.
    """

    def __init__(self, scripted_outcomes: Mapping[str, FakeAgentOutcome]) -> None:
        self._scripted = dict(scripted_outcomes)
        self.calls: list[AgentRequest] = []

    def run(self, request: AgentRequest) -> AgentResult:
        self.calls.append(request)
        if request.request_id not in self._scripted:
            raise KeyError(f"FakeAgentRunner has no scripted outcome for request {request.request_id!r}")

        outcome = self._scripted[request.request_id]
        if outcome.status is AgentExecutionStatus.SUCCEEDED:
            if outcome.structured_report is None:
                raise ValueError("successful FakeAgentOutcome requires structured_report")
            return build_successful_agent_result(
                request=request,
                execution_id=outcome.execution_id,
                structured_report=outcome.structured_report,
                session_reference=outcome.session_reference,
                diagnostics=outcome.diagnostics,
            )

        return AgentResult(
            execution_id=outcome.execution_id,
            request_id=request.request_id,
            role=request.role,
            provider=request.provider,
            context=request.context,
            execution_status=outcome.status,
            session_reference=outcome.session_reference,
            diagnostics=outcome.diagnostics,
        )
