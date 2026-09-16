from __future__ import annotations

from sdd_agent.diagnostics.errors import ConfigurationError, TechnicalErrorCategory
from sdd_agent.diagnostics.model import Diagnostic, format_diagnostic


def test_technical_error_carries_category_and_details() -> None:
    error = ConfigurationError(
        "bad config",
        details={"path": "sdd.yaml"},
        task_id="T001",
        attempt_id="001",
    )

    assert error.category is TechnicalErrorCategory.CONFIGURATION
    assert error.details == {"path": "sdd.yaml"}
    assert error.task_id == "T001"
    assert error.attempt_id == "001"


def test_technical_error_converts_to_diagnostic() -> None:
    error = ConfigurationError("bad config", task_id="T001", attempt_id="001")

    diagnostic = error.to_diagnostic()

    assert isinstance(diagnostic, Diagnostic)
    assert diagnostic.category is TechnicalErrorCategory.CONFIGURATION
    assert diagnostic.message == "bad config"
    assert diagnostic.task_id == "T001"
    assert diagnostic.attempt_id == "001"


def test_format_diagnostic_includes_correlation_and_category() -> None:
    diagnostic = Diagnostic(
        category=TechnicalErrorCategory.CONFIGURATION,
        message="bad config",
        task_id="T001",
        attempt_id="001",
    )

    assert format_diagnostic(diagnostic) == "[T001/001][ConfigurationError] bad config"


def test_format_diagnostic_without_correlation() -> None:
    diagnostic = Diagnostic(
        category=TechnicalErrorCategory.WORKFLOW_VIOLATION,
        message="lock already held",
    )

    assert format_diagnostic(diagnostic) == "[-][WorkflowViolation] lock already held"


def test_format_diagnostic_with_task_id_only() -> None:
    diagnostic = Diagnostic(
        category=TechnicalErrorCategory.PERSISTENCE,
        message="write failed",
        task_id="T001",
    )

    assert format_diagnostic(diagnostic) == "[T001][PersistenceError] write failed"


def test_format_diagnostic_renders_sorted_details() -> None:
    diagnostic = Diagnostic(
        category=TechnicalErrorCategory.PERSISTENCE,
        message="write failed",
        details={"path": "/tmp/x", "attempt": 2},
    )

    assert format_diagnostic(diagnostic) == "[-][PersistenceError] write failed (attempt=2, path=/tmp/x)"
