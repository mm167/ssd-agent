"""ReadinessReport (SPEC Section 13; PLAN Section 12 evidence-type example).

READINESS's conceptual outcomes (SPEC Section 13: READY_FOR_CODE,
SPEC_REQUIRED, PLAN_REQUIRED, TASKS_REQUIRED, BLOCKED) are represented as a
boolean `ready_for_code` flag plus an optional `Condition`, following PLAN's
Phase/Condition/NextAction separation (PLAN Section 9) rather than one
combined enum. Computing *which* outcome applies is ReadinessPolicy's
responsibility (T005); this model only fixes the shape of the recorded
outcome and its own internal consistency.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ConfigDict, Field, model_validator

from sdd_agent.domain.models.enums import Condition
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.schema import SchemaVersioned


class ReadinessReport(SchemaVersioned):
    """Durable outcome of one READINESS evaluation for an Attempt (SPEC
    Section 13). No candidate exists yet at READINESS time, so `context`
    carries no `candidate_id`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(min_length=1)
    context: EvidenceContext
    ready_for_code: bool
    condition: Condition | None = None
    rationale: str = Field(min_length=1)
    produced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _ready_flag_matches_condition(self) -> "ReadinessReport":
        if self.ready_for_code and self.condition is not None:
            raise ValueError("ready_for_code=True must not carry a blocking condition")
        if not self.ready_for_code and self.condition is None:
            raise ValueError("ready_for_code=False requires a condition explaining why")
        return self
