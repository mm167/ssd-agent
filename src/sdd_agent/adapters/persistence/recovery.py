"""Recovery loader (TASKS T003 Deliverable: "Recovery loader"; SPEC Sections
51-53; PLAN Sections 72-73, 106).

`load_recovered_state` reconstructs the durable `.sdd/` state for one task
using only a `PersistenceStore` -- no AI conversation and no reference to a
previously constructed Python object is required, satisfying SPEC Section
51 ("SDD Agent must survive orchestrator restart without requiring previous
AI conversations").

This module intentionally stops at reconstructing what `.sdd/` itself
records (the current Attempt pointer plus its event journal). It does not:

- reconcile that state against the actual Git repository, which requires
  `GitRepository` (T004);
- decide RESUME vs. REPOSITORY_MISMATCH vs. RESTART, which is workflow
  policy (T005/T011);
- reconstruct agent/session continuity (T008).

Individual durable evidence reports (readiness, validation, review,
waivers, human decisions, CI, implementation reports) remain available
on demand through `PersistenceStore.load_reports`/`load_report` once a
caller knows which category and candidate it needs; bundling all of them
unconditionally here would presume policy this TASK does not own.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from sdd_agent.domain.models.attempt import Attempt
from sdd_agent.domain.models.event import WorkflowEvent
from sdd_agent.ports.persistence import PersistenceStore


class RecoveredWorkflowState(BaseModel):
    """The durable `.sdd/` state reconstructable for one task without any AI
    conversation (SPEC Section 52)."""

    model_config = ConfigDict(extra="forbid")

    attempt: Attempt
    events: list[WorkflowEvent]


def load_recovered_state(store: PersistenceStore, task_id: str) -> RecoveredWorkflowState | None:
    """Reconstruct the current Attempt and its event journal for `task_id`.

    Returns `None` when there is no current Attempt at all, or when the
    persisted current Attempt belongs to a different task: V1 tracks a
    single current-pointer at a time (PLAN Section 59 Single Active
    Execution), so a mismatched `task_id` means nothing is currently
    recoverable for the requested task.
    """
    attempt = store.load_current()
    if attempt is None or attempt.task_id != task_id:
        return None

    events = store.read_events(attempt.task_id, attempt.attempt_id)
    return RecoveredWorkflowState(attempt=attempt, events=events)
