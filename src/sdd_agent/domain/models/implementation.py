"""ImplementationReport (PLAN Section 90A; TASKS T002 acceptance criterion:
"ImplementationReport is candidate-bound in its model contract").

`completion_status = COMPLETED` means only that the implementer declares the
exact referenced candidate complete for the active TASK scope. It proves
neither TASK correctness, validation success, review success, nor
READY_FOR_REVIEW -- computing READY_FOR_REVIEW from this and other facts
belongs to the Orchestrator (T005/T011), not to this model or to the
implementer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ConfigDict, Field, model_validator

from sdd_agent.configuration.models import AgentRole
from sdd_agent.domain.models.enums import ImplementationCompletionStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.schema import SchemaVersioned


class ImplementationReport(SchemaVersioned):
    """A candidate-bound declaration that IMPLEMENTATION or FIX completed for
    the active TASK scope (PLAN Section 90A).

    `context.candidate_id` is required: if the candidate changes after this
    report is produced, the report becomes non-applicable to the changed
    candidate (PLAN Section 90A), which is exactly what a required
    `candidate_id` makes checkable via `EvidenceContext.applies_to`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(min_length=1)
    context: EvidenceContext
    implementation_role: AgentRole
    completion_status: ImplementationCompletionStatus
    changed_paths: list[str] = Field(default_factory=list)
    task_scope_summary: str = Field(min_length=1)
    validations_run_by_agent: list[str] = Field(default_factory=list)
    known_limitations: str | None = None
    produced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _candidate_required(self) -> "ImplementationReport":
        if self.context.candidate_id is None:
            raise ValueError("ImplementationReport.context.candidate_id is required")
        return self
