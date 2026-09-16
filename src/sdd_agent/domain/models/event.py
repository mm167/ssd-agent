"""Workflow event journal record (SPEC Section 54 traceability history; PLAN
Section 68 Event Journal).

`WorkflowEvent` is deliberately lighter than the candidate-bound evidence
models in this package: PLAN Section 68 explicitly disclaims full Event
Sourcing, and Section 84 only requires events to be correlatable by
`task_id`/`attempt_id` (and optionally `candidate_id`), not bound to a full
`EvidenceContext`. `event_type` is an open, implementer-defined string --
like `NextAuthorizedAction.action` -- because PLAN Section 68's conceptual
event list (`ATTEMPT_STARTED`, `READINESS_COMPLETED`, ...) is illustrative,
and later TASKS will introduce further event types. Deciding which events a
given transition must emit is workflow behavior owned by later TASKS
(T005/T011/T012/T013/T016); this module only fixes the durable record shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ConfigDict, Field

from sdd_agent.domain.models.schema import SchemaVersioned


class WorkflowEvent(SchemaVersioned):
    """One immutable, append-only journal entry (PLAN Section 68)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    candidate_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
