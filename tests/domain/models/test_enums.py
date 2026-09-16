from __future__ import annotations

from sdd_agent.domain.models import (
    CIStatus,
    Condition,
    FindingRoute,
    FindingSeverity,
    HumanDecisionType,
    ImplementationCompletionStatus,
    Phase,
    ProblemClassification,
    ValidationStatus,
    WaiverEligibleCause,
)


def test_finding_severity_is_exactly_three_values() -> None:
    assert {member.value for member in FindingSeverity} == {"blocker", "important", "minor"}


def test_validation_status_is_exactly_three_values() -> None:
    assert {member.value for member in ValidationStatus} == {"passed", "failed", "not_run"}


def test_ci_status_is_exactly_six_values() -> None:
    assert {member.value for member in CIStatus} == {
        "pending",
        "running",
        "green",
        "failed",
        "cancelled",
        "not_found",
    }


def test_waiver_eligible_cause_is_exactly_environment() -> None:
    assert {member.value for member in WaiverEligibleCause} == {"environment"}


def test_finding_route_excludes_repository_mismatch() -> None:
    assert "repository_mismatch" not in {member.value for member in FindingRoute}


def test_problem_classification_includes_repository_mismatch() -> None:
    assert "repository_mismatch" in {member.value for member in ProblemClassification}


def test_condition_includes_task_dependency_unsatisfied() -> None:
    assert Condition.TASK_DEPENDENCY_UNSATISFIED.value == "task_dependency_unsatisfied"


def test_phase_and_human_decision_type_are_string_enums() -> None:
    assert Phase.CLOSED.value == "closed"
    assert HumanDecisionType.ABANDON.value == "abandon"


def test_implementation_completion_status_is_exactly_three_values() -> None:
    assert {member.value for member in ImplementationCompletionStatus} == {
        "completed",
        "incomplete",
        "failed",
    }
