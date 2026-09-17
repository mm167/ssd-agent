"""`ClassificationReport` and `RoutingPolicy` (SPEC Sections 7, 14, 16, 20, 29,
35.6, 41-44; PLAN Sections 42-46).

Classification (what kind of problem this is) and routing (where it must go
next) are deliberately kept separate (SPEC Section 7; PLAN Section 45):
`RoutingPolicy.route` is a pure, closed-map function from
`ProblemClassification` to `Condition`. Producing a `ClassificationReport` in
the first place -- whether by a deterministic rule or by an AI agent's
semantic analysis (PLAN Section 43) -- is orchestration behavior owned by
later TASKS (T011/T016); this module only fixes the report shape every one of
those TASKS must produce and the single deterministic map every one of them
must route through. An agent's free-form classification prose has no routing
authority of its own; only a validated `ProblemClassification` value does.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ConfigDict, Field

from sdd_agent.domain.models.enums import Condition, FindingRoute, ProblemClassification
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.schema import SchemaVersioned


class ClassificationReport(SchemaVersioned):
    """A durable, explainable classification of one problem (PLAN Section 44)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(min_length=1)
    context: EvidenceContext
    classification: ProblemClassification
    rationale: str = Field(min_length=1)
    evidence: str | None = None
    classifier_metadata: dict[str, Any] = Field(default_factory=dict)
    produced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


_ROUTING_MAP: dict[ProblemClassification, Condition] = {
    ProblemClassification.PRODUCT: Condition.SPEC_REQUIRED,
    ProblemClassification.ARCHITECTURE: Condition.PLAN_REQUIRED,
    ProblemClassification.TASKS: Condition.TASKS_REQUIRED,
    ProblemClassification.CODE: Condition.FIX_REQUIRED,
    ProblemClassification.ENVIRONMENT: Condition.ENVIRONMENT_BLOCKED,
    ProblemClassification.REPOSITORY_MISMATCH: Condition.REPOSITORY_MISMATCH,
}

_FINDING_ROUTE_TO_CLASSIFICATION: dict[FindingRoute, ProblemClassification] = {
    FindingRoute.PRODUCT: ProblemClassification.PRODUCT,
    FindingRoute.ARCHITECTURE: ProblemClassification.ARCHITECTURE,
    FindingRoute.TASKS: ProblemClassification.TASKS,
    FindingRoute.CODE: ProblemClassification.CODE,
    FindingRoute.ENVIRONMENT: ProblemClassification.ENVIRONMENT,
}


class RoutingPolicy:
    """Deterministic classification -> Condition routing (SPEC Section 7;
    PLAN Section 45).

    The same closed map serves every routing context this SPEC describes
    (READINESS ambiguity Section 14, implementation artifact return Section
    16, validation failure Section 20, human-requested change Section 35.6,
    and CI failure classification Sections 41-44): each of those sections
    routes an identical `ProblemClassification` set to an identical
    `Condition` set.
    """

    @staticmethod
    def route(classification: ProblemClassification) -> Condition:
        return _ROUTING_MAP[classification]

    @staticmethod
    def route_report(report: ClassificationReport) -> Condition:
        return RoutingPolicy.route(report.classification)

    @staticmethod
    def route_finding(route: FindingRoute) -> Condition:
        """Route a review Finding (SPEC Section 29) through the same map.

        `FindingRoute` deliberately excludes `REPOSITORY_MISMATCH` (a mismatch
        is detected structurally, never raised as a review finding -- SPEC
        Section 48), so this can never require that branch of the map.
        """
        return RoutingPolicy.route(_FINDING_ROUTE_TO_CLASSIFICATION[route])
