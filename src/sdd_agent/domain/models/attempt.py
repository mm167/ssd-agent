"""Attempt, phase/condition state, and next-authorized-action representation
(PLAN Sections 9, 10).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from sdd_agent.domain.models.enums import Condition, Phase
from sdd_agent.domain.models.schema import SchemaVersioned


class NextAuthorizedAction(BaseModel):
    """What the user or orchestrator is currently allowed/required to do next
    (PLAN Section 9.3). `action` is an implementer-defined action identifier
    (e.g. "RESOLVE_ENVIRONMENT"); the closed set of valid actions is a gate
    concern owned by T005, not a value this model constrains.
    """

    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=1)
    reason: str | None = None


class Attempt(SchemaVersioned):
    """The durable execution container for one TASK execution attempt (PLAN
    Section 10).

    This is the mutable *current* pointer (PLAN Section 66), distinct from
    the immutable historical evidence (ReadinessReport, ValidationResult,
    ReviewReport, HumanDecision, CIResult, ImplementationReport) it relates
    to only by shared `task_id`/`attempt_id` identity (PLAN Section 12) --
    those records are not embedded here. Storing/loading Attempt state and
    reconstructing it from `.sdd/` on restart belongs to T003.
    """

    model_config = ConfigDict(extra="forbid")

    attempt_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    phase: Phase
    condition: Condition | None = None
    next_authorized_action: NextAuthorizedAction | None = None
    baseline_sha: str = Field(min_length=1)
    candidate_id: str | None = None
