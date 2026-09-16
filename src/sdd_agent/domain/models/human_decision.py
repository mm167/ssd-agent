"""Structured human decisions (SPEC Sections 5.1, 22, 35-37; PLAN Section 54).

`HumanDecision` is immutable, append-only evidence (PLAN Section 67).
Whether a previously recorded decision is still *applicable* to the current
candidate/attempt/contract is therefore never a field stored on the decision
itself -- it is recomputed by comparing `context` against the current
workflow context (PLAN Section 71 "Gate Reconstruction": remembering a
decision was made is not the same as proving it is still applicable). That
comparison belongs to T005/T012, using `EvidenceContext.applies_to`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ConfigDict, Field

from sdd_agent.domain.models.enums import HumanDecisionType
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.schema import SchemaVersioned


class HumanDecision(SchemaVersioned):
    """A durable record of one explicit human decision (PLAN Section 54)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    decision_type: HumanDecisionType
    context: EvidenceContext
    choice: str = Field(min_length=1)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
