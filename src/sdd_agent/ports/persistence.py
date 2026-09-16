"""`PersistenceStore` port (TASKS T003 Deliverable: "Persistence port and
local filesystem adapter"; PLAN Sections 63-71, 100-101).

Core and later-TASK orchestration code shall depend on this abstraction, not
on JSON/filesystem details directly (PLAN Section 101 dependency direction).
`LocalPersistenceStore` (`sdd_agent.adapters.persistence.local_store`) is the
concrete V1 implementation.

This port only defines *how workflow state and evidence are stored and
retrieved*. It does not decide workflow policy, Git reconciliation, or
gate applicability -- those remain T004/T005/T011 responsibilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from sdd_agent.domain.models.attempt import Attempt
from sdd_agent.domain.models.event import WorkflowEvent

ReportT = TypeVar("ReportT", bound=BaseModel)


class PersistenceStore(ABC):
    """Provider-neutral contract for `.sdd/` workflow state (PLAN Section 65).

    Two distinct durability guarantees are exposed (PLAN Section 66-67):

    - the *current* pointer (`save_current`/`load_current`) is a mutable
      snapshot that may be overwritten as the active Attempt progresses;
    - *reports*, the *attempt record*, and *events* are append-only: an
      implementation must refuse to silently overwrite previously written
      historical evidence.
    """

    @abstractmethod
    def save_current(self, attempt: Attempt) -> None:
        """Overwrite the current-workflow-pointer snapshot (PLAN Section 66)."""

    @abstractmethod
    def load_current(self) -> Attempt | None:
        """Load the current-workflow-pointer snapshot, or `None` if absent."""

    @abstractmethod
    def save_attempt_record(self, attempt: Attempt) -> None:
        """Persist the immutable Attempt-created record for one Attempt.

        Must raise `sdd_agent.diagnostics.errors.PersistenceError` if a
        record already exists for this `(task_id, attempt_id)`.
        """

    @abstractmethod
    def load_attempt_record(self, task_id: str, attempt_id: str) -> Attempt | None:
        """Load the immutable Attempt record, or `None` if absent."""

    @abstractmethod
    def append_event(self, event: WorkflowEvent) -> None:
        """Append one event to the Attempt's event journal (PLAN Section 68)."""

    @abstractmethod
    def read_events(self, task_id: str, attempt_id: str) -> list[WorkflowEvent]:
        """Read the full event journal for one Attempt, in append order."""

    @abstractmethod
    def append_report(
        self,
        task_id: str,
        attempt_id: str,
        category: str,
        report_id: str,
        report: BaseModel,
    ) -> None:
        """Persist one immutable historical report (PLAN Section 67).

        Must raise `PersistenceError` if a report already exists for this
        `(task_id, attempt_id, category, report_id)`.
        """

    @abstractmethod
    def load_report(
        self,
        task_id: str,
        attempt_id: str,
        category: str,
        report_id: str,
        model_type: type[ReportT],
    ) -> ReportT:
        """Load one previously appended report, validated as `model_type`."""

    @abstractmethod
    def list_report_ids(self, task_id: str, attempt_id: str, category: str) -> list[str]:
        """List report ids in a category, in a deterministic (sorted) order."""

    @abstractmethod
    def load_reports(
        self,
        task_id: str,
        attempt_id: str,
        category: str,
        model_type: type[ReportT],
    ) -> list[ReportT]:
        """Load every report in a category, in deterministic order."""
