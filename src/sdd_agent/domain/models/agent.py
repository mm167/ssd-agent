"""Provider-neutral agent execution evidence (TASKS T007; PLAN Sections 13,
15, 18, 90A, 96.4, 97).

These models describe what the Core may ask from an agent and what evidence
comes back. They deliberately contain no Claude Code or Codex process details:
provider-specific invocation belongs to T009/T010 adapters, while later
orchestration and session-policy decisions belong to T008/T011.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sdd_agent.configuration.models import AgentProvider, AgentRole
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.implementation import ImplementationReport
from sdd_agent.domain.models.readiness import ReadinessReport
from sdd_agent.domain.models.review import ReviewReport
from sdd_agent.domain.models.schema import SchemaVersioned


class AgentReportType(StrEnum):
    """Structured report kinds an agent request may require."""

    READINESS_REPORT = "readiness_report"
    IMPLEMENTATION_REPORT = "implementation_report"
    REVIEW_REPORT = "review_report"


class AgentExecutionStatus(StrEnum):
    """Closed technical outcomes for one agent execution.

    Only `SUCCEEDED` may carry structured report evidence. Failure-like
    statuses are technical facts for later classification/routing; they are
    not successful workflow evidence.
    """

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    MALFORMED_OUTPUT = "malformed_output"


AgentStructuredReport: TypeAlias = ReadinessReport | ImplementationReport | ReviewReport


class AgentRequest(SchemaVersioned):
    """Provider-neutral request sent through the `AgentRunner` port."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    role: AgentRole
    provider: AgentProvider
    repository: Path
    task_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    context: EvidenceContext
    instructions: str = Field(min_length=1)
    expected_report_type: AgentReportType
    session_policy: str | None = None

    @model_validator(mode="after")
    def _context_matches_request_identity(self) -> "AgentRequest":
        if self.context.task_id != self.task_id:
            raise ValueError("AgentRequest.context.task_id must match task_id")
        if self.context.attempt_id != self.attempt_id:
            raise ValueError("AgentRequest.context.attempt_id must match attempt_id")
        return self


class AgentResult(SchemaVersioned):
    """Provider-neutral result returned by `AgentRunner`.

    The result is bound to the role/provider/context that produced it, but
    deterministic workflow policies decide whether the evidence can authorize
    any transition.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    role: AgentRole
    provider: AgentProvider
    context: EvidenceContext
    execution_status: AgentExecutionStatus
    report_type: AgentReportType | None = None
    structured_report: AgentStructuredReport | None = None
    session_reference: str | None = None
    diagnostics: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _report_matches_execution_status(self) -> "AgentResult":
        if self.execution_status is AgentExecutionStatus.SUCCEEDED:
            if self.structured_report is None:
                raise ValueError("successful AgentResult requires structured_report")
            if self.report_type is None:
                raise ValueError("successful AgentResult requires report_type")
            if not self.structured_report.context.applies_to(self.context):
                raise ValueError("AgentResult structured_report context must match result context")
            if self._actual_report_type() is not self.report_type:
                raise ValueError("AgentResult report_type must match structured_report type")
            if (
                isinstance(self.structured_report, ImplementationReport)
                and self.structured_report.implementation_role is not self.role
            ):
                raise ValueError("ImplementationReport.implementation_role must match AgentResult.role")
        else:
            if self.structured_report is not None:
                raise ValueError("failed agent execution must not carry successful structured_report evidence")
            if self.report_type is not None:
                raise ValueError("failed agent execution must not carry report_type")
        return self

    def _actual_report_type(self) -> AgentReportType:
        if isinstance(self.structured_report, ReadinessReport):
            return AgentReportType.READINESS_REPORT
        if isinstance(self.structured_report, ImplementationReport):
            return AgentReportType.IMPLEMENTATION_REPORT
        if isinstance(self.structured_report, ReviewReport):
            return AgentReportType.REVIEW_REPORT
        raise AssertionError("unreachable validated AgentStructuredReport type")


def report_type_for(report: AgentStructuredReport) -> AgentReportType:
    """Return the declared agent-report kind for a validated report model."""

    if isinstance(report, ReadinessReport):
        return AgentReportType.READINESS_REPORT
    if isinstance(report, ImplementationReport):
        return AgentReportType.IMPLEMENTATION_REPORT
    if isinstance(report, ReviewReport):
        return AgentReportType.REVIEW_REPORT
    raise TypeError(f"unsupported agent structured report type: {type(report).__name__}")


def build_successful_agent_result(
    *,
    request: AgentRequest,
    execution_id: str,
    structured_report: AgentStructuredReport,
    session_reference: str | None = None,
    diagnostics: tuple[str, ...] = (),
) -> AgentResult:
    """Validate and bind a successful structured report to its request.

    This is the T007 report-validation hook used by fake and future concrete
    adapters before returning success evidence to the Core.
    """

    actual_report_type = report_type_for(structured_report)
    if actual_report_type is not request.expected_report_type:
        raise ValueError(
            "agent structured_report type does not match request.expected_report_type: "
            f"{actual_report_type.value} != {request.expected_report_type.value}"
        )
    if not structured_report.context.applies_to(request.context):
        raise ValueError("agent structured_report context does not match request context")
    if (
        isinstance(structured_report, ImplementationReport)
        and structured_report.implementation_role is not request.role
    ):
        raise ValueError("ImplementationReport.implementation_role must match AgentRequest.role")

    return AgentResult(
        execution_id=execution_id,
        request_id=request.request_id,
        role=request.role,
        provider=request.provider,
        context=request.context,
        execution_status=AgentExecutionStatus.SUCCEEDED,
        report_type=actual_report_type,
        structured_report=structured_report,
        session_reference=session_reference,
        diagnostics=diagnostics,
    )
