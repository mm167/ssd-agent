"""Operational log model, kept distinct from durable SDD evidence (PLAN Section 83).

Examples of operational logs: "Launching Codex", "Retry 1/3", "Polling CI".
These aid diagnosis but do not automatically satisfy workflow gates. Durable
evidence (ReviewReport, ValidationReport, HumanDecision, ...) is a separate
model family owned by later TASKS.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class OperationalLogEvent(BaseModel):
    """A single operational log line, correlatable to a task/attempt.

    An OperationalLogEvent is never treated as SDD evidence.
    """

    model_config = ConfigDict(extra="forbid")

    level: LogLevel
    message: str
    task_id: str | None = None
    attempt_id: str | None = None
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def format_log_event(event: OperationalLogEvent) -> str:
    """Render an OperationalLogEvent using the PLAN Section 84 correlation prefix."""
    if event.task_id and event.attempt_id:
        correlation = f"[{event.task_id}/{event.attempt_id}]"
    elif event.task_id:
        correlation = f"[{event.task_id}]"
    else:
        correlation = "[-]"
    return f"{correlation}[{event.level.value}] {event.message}"
