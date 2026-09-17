from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models.enums import Condition, FindingRoute, ProblemClassification
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.routing.classification import ClassificationReport, RoutingPolicy


def _context() -> EvidenceContext:
    return EvidenceContext(task_id="T005", attempt_id="a1")


@pytest.mark.parametrize(
    ("classification", "expected"),
    [
        (ProblemClassification.PRODUCT, Condition.SPEC_REQUIRED),
        (ProblemClassification.ARCHITECTURE, Condition.PLAN_REQUIRED),
        (ProblemClassification.TASKS, Condition.TASKS_REQUIRED),
        (ProblemClassification.CODE, Condition.FIX_REQUIRED),
        (ProblemClassification.ENVIRONMENT, Condition.ENVIRONMENT_BLOCKED),
        (ProblemClassification.REPOSITORY_MISMATCH, Condition.REPOSITORY_MISMATCH),
    ],
)
def test_route_is_a_total_deterministic_map(
    classification: ProblemClassification, expected: Condition
) -> None:
    assert RoutingPolicy.route(classification) is expected


def test_route_is_deterministic_across_calls() -> None:
    for classification in ProblemClassification:
        assert RoutingPolicy.route(classification) is RoutingPolicy.route(classification)


def test_route_report_delegates_to_route() -> None:
    report = ClassificationReport(
        report_id="c1",
        context=_context(),
        classification=ProblemClassification.CODE,
        rationale="failing assertion in candidate code",
    )

    assert RoutingPolicy.route_report(report) is Condition.FIX_REQUIRED


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        (FindingRoute.PRODUCT, Condition.SPEC_REQUIRED),
        (FindingRoute.ARCHITECTURE, Condition.PLAN_REQUIRED),
        (FindingRoute.TASKS, Condition.TASKS_REQUIRED),
        (FindingRoute.CODE, Condition.FIX_REQUIRED),
        (FindingRoute.ENVIRONMENT, Condition.ENVIRONMENT_BLOCKED),
    ],
)
def test_route_finding_matches_finding_route_semantics(route: FindingRoute, expected: Condition) -> None:
    assert RoutingPolicy.route_finding(route) is expected


def test_classification_report_requires_rationale() -> None:
    with pytest.raises(ValidationError):
        ClassificationReport(
            report_id="c1",
            context=_context(),
            classification=ProblemClassification.CODE,
            rationale="",
        )


def test_classification_report_is_frozen() -> None:
    report = ClassificationReport(
        report_id="c1",
        context=_context(),
        classification=ProblemClassification.CODE,
        rationale="failing assertion",
    )

    with pytest.raises(ValidationError):
        report.classification = ProblemClassification.ENVIRONMENT  # type: ignore[misc]
