"""Diagnostic model and formatting (PLAN Sections 83, 84, 87).

A Diagnostic explains a technical condition to a human or log stream. It is
explicitly not SDD evidence (PLAN Section 83): it aids diagnosis but never
automatically satisfies a workflow gate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sdd_agent.diagnostics.errors import TechnicalErrorCategory


class Diagnostic(BaseModel):
    """A structured, explainable technical diagnostic."""

    model_config = ConfigDict(extra="forbid")

    category: TechnicalErrorCategory
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    task_id: str | None = None
    attempt_id: str | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def format_diagnostic(diagnostic: Diagnostic) -> str:
    """Render a Diagnostic as a single correlatable line.

    Conceptual format (PLAN Section 84)::

        [task_id/attempt_id][CATEGORY] message (key=value, ...)
    """
    if diagnostic.task_id and diagnostic.attempt_id:
        correlation = f"[{diagnostic.task_id}/{diagnostic.attempt_id}]"
    elif diagnostic.task_id:
        correlation = f"[{diagnostic.task_id}]"
    else:
        correlation = "[-]"

    line = f"{correlation}[{diagnostic.category.value}] {diagnostic.message}"

    if diagnostic.details:
        rendered_details = ", ".join(
            f"{key}={value}" for key, value in sorted(diagnostic.details.items(), key=lambda item: item[0])
        )
        line = f"{line} ({rendered_details})"

    return line
