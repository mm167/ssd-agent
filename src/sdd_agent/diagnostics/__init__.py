"""Structured diagnostics and technical error surfaces (PLAN Sections 83, 84, 87)."""

from sdd_agent.diagnostics.errors import (
    AgentExecutionError,
    CIProviderError,
    ConfigurationError,
    GitOperationError,
    PersistenceError,
    SddTechnicalError,
    TechnicalErrorCategory,
    ValidationExecutionError,
    WorkflowViolation,
)
from sdd_agent.diagnostics.logs import LogLevel, OperationalLogEvent, format_log_event
from sdd_agent.diagnostics.model import Diagnostic, format_diagnostic

__all__ = [
    "AgentExecutionError",
    "CIProviderError",
    "ConfigurationError",
    "Diagnostic",
    "GitOperationError",
    "LogLevel",
    "OperationalLogEvent",
    "PersistenceError",
    "SddTechnicalError",
    "TechnicalErrorCategory",
    "ValidationExecutionError",
    "WorkflowViolation",
    "format_diagnostic",
    "format_log_event",
]
