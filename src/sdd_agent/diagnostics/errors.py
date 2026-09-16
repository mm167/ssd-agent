"""Technical error model (PLAN Section 87).

Technical errors and SDD problem classifications (PRODUCT, ARCHITECTURE,
TASKS, CODE, ENVIRONMENT, REPOSITORY_MISMATCH) are distinct concepts. This
module only defines the technical-error side; mapping a technical error onto
a problem classification is later workflow logic, not something a technical
error decides about itself.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sdd_agent.diagnostics.model import Diagnostic


class TechnicalErrorCategory(StrEnum):
    """Conceptual technical error families (PLAN Section 87)."""

    CONFIGURATION = "ConfigurationError"
    PERSISTENCE = "PersistenceError"
    AGENT_EXECUTION = "AgentExecutionError"
    GIT_OPERATION = "GitOperationError"
    VALIDATION_EXECUTION = "ValidationExecutionError"
    CI_PROVIDER = "CIProviderError"
    WORKFLOW_VIOLATION = "WorkflowViolation"


class SddTechnicalError(Exception):
    """Base class for a structured, explainable technical error.

    Every subclass fixes its own `category`, carries a human-readable
    `message`, optional structured `details`, and optional correlation
    identifiers so the error can be traced back to a task/attempt
    (PLAN Section 84).
    """

    category: TechnicalErrorCategory

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        task_id: str | None = None,
        attempt_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.task_id = task_id
        self.attempt_id = attempt_id

    def to_diagnostic(self) -> "Diagnostic":
        """Convert this technical error into a formattable Diagnostic."""
        from sdd_agent.diagnostics.model import Diagnostic

        return Diagnostic(
            category=self.category,
            message=self.message,
            details=self.details,
            task_id=self.task_id,
            attempt_id=self.attempt_id,
        )


class ConfigurationError(SddTechnicalError):
    category = TechnicalErrorCategory.CONFIGURATION


class PersistenceError(SddTechnicalError):
    category = TechnicalErrorCategory.PERSISTENCE


class AgentExecutionError(SddTechnicalError):
    category = TechnicalErrorCategory.AGENT_EXECUTION


class GitOperationError(SddTechnicalError):
    category = TechnicalErrorCategory.GIT_OPERATION


class ValidationExecutionError(SddTechnicalError):
    category = TechnicalErrorCategory.VALIDATION_EXECUTION


class CIProviderError(SddTechnicalError):
    category = TechnicalErrorCategory.CI_PROVIDER


class WorkflowViolation(SddTechnicalError):
    category = TechnicalErrorCategory.WORKFLOW_VIOLATION
