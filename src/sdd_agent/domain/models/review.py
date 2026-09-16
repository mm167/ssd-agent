"""Review findings and report (SPEC Sections 25-31; PLAN Section 39).

T002 owns only the data shape. Computing the deterministic review gate
(BLOCKER == 0 AND IMPORTANT == 0) and routing findings to SPEC/PLAN/TASKS/
CODE/ENVIRONMENT belongs to T005's ReviewGatePolicy/RoutingPolicy and T011's
orchestration, not to this module.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sdd_agent.domain.models.enums import FindingRoute, FindingSeverity
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.schema import SchemaVersioned


class Finding(BaseModel):
    """A single structured review finding (SPEC Section 28; PLAN Section 39)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_id: str = Field(min_length=1)
    severity: FindingSeverity
    route: FindingRoute | None = None
    summary: str = Field(min_length=1)
    evidence: str | None = None
    rationale: str | None = None


class ReviewReport(SchemaVersioned):
    """The exact-candidate outcome of one independent REVIEW or RE-REVIEW
    (SPEC Sections 25-30; PLAN Section 39).

    `context.candidate_id` is required: review evidence applies only to the
    exact candidate reviewed (SPEC INV-12).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(min_length=1)
    context: EvidenceContext
    findings: list[Finding] = Field(default_factory=list)
    produced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _candidate_required(self) -> "ReviewReport":
        if self.context.candidate_id is None:
            raise ValueError("ReviewReport.context.candidate_id is required")
        return self
