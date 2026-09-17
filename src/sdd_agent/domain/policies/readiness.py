"""`ReadinessPolicy` (SPEC Sections 9, 13-14; PLAN Sections 45-46).

Computes the deterministic READINESS outcome from already-established facts.
It does not itself discover dependency status, inspect the repository, or
decide whether an artifact is ambiguous -- those facts are supplied by the
caller (T004 for repository facts; a later TASK's classification for artifact
ambiguity, PLAN Section 43). This module only fixes the deterministic
decision those facts must produce, matching `ReadinessReport`'s own
`ready_for_code`/`condition` invariant (T002).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.domain.models.enums import Condition, ProblemClassification
from sdd_agent.domain.routing.classification import RoutingPolicy

_READINESS_ARTIFACT_AMBIGUITY_CLASSIFICATIONS: frozenset[ProblemClassification] = frozenset(
    {
        ProblemClassification.PRODUCT,
        ProblemClassification.ARCHITECTURE,
        ProblemClassification.TASKS,
    }
)
"""The only classifications READINESS artifact ambiguity may carry (SPEC
Section 14, verbatim: "PRODUCT -> SPEC_REQUIRED, ARCHITECTURE -> PLAN_REQUIRED,
TASKS -> TASKS_REQUIRED"). `CODE` has no meaning before CODE is authorized;
`ENVIRONMENT` and `REPOSITORY_MISMATCH` are handled by this policy's own
`repository_mismatch` parameter and by validation-failure classification
(SPEC Section 20), never by this parameter. `RoutingPolicy.route` is total
over every `ProblemClassification`, so without this explicit restriction an
incompatible value would silently produce a normal-looking (but SPEC-Section-
14-incompatible) route such as `FIX_REQUIRED` instead of failing.
"""


def dependencies_satisfied(dependency_task_ids: Iterable[str], closed_task_ids: Collection[str]) -> bool:
    """Whether every mandatory dependency TASK is CLOSED (SPEC Section 9, INV-24).

    Task numeric order is irrelevant; only closure of the exact listed
    dependency ids matters (SPEC Section 60: "dependency satisfaction
    requires the dependency TASK to be CLOSED").
    """
    return all(dependency_id in closed_task_ids for dependency_id in dependency_task_ids)


@dataclass(frozen=True, slots=True)
class ReadinessDecision:
    """The deterministic READINESS outcome (SPEC Section 13).

    Mirrors `ReadinessReport`'s own invariant: `ready_for_code=True` never
    carries a `condition`, and `ready_for_code=False` always does.
    """

    ready_for_code: bool
    condition: Condition | None
    reasons: tuple[str, ...] = ()


class ReadinessPolicy:
    """Deterministic READINESS gate (SPEC Section 13)."""

    @staticmethod
    def evaluate(
        *,
        dependency_contract_valid: bool,
        dependencies_satisfied: bool,
        artifact_ambiguity: ProblemClassification | None = None,
        repository_mismatch: bool = False,
    ) -> ReadinessDecision:
        """Evaluate in the precedence SPEC Sections 9-14 establish:

        1. an existing repository mismatch (SPEC Section 10) blocks
           everything, since baseline/candidate identity is not even
           trustworthy yet;
        2. an incorrect/missing TASKS dependency contract routes to
           `TASKS_REQUIRED` rather than being silently repaired (SPEC
           Section 9);
        3. an unsatisfied (but correctly declared) dependency blocks with
           `TASK_DEPENDENCY_UNSATISFIED` (SPEC Section 9);
        4. remaining SPEC/PLAN/TASKS ambiguity routes through
           `RoutingPolicy` (SPEC Section 14).

        Only when none of these apply is CODE authorized.

        `artifact_ambiguity` is restricted to `PRODUCT`, `ARCHITECTURE`, and
        `TASKS` (SPEC Section 14); any other classification raises
        `WorkflowViolation` rather than being silently routed as if it were
        one of those three.
        """
        if repository_mismatch:
            return ReadinessDecision(
                False,
                Condition.REPOSITORY_MISMATCH,
                ("repository state is incompatible with the expected attempt context",),
            )
        if not dependency_contract_valid:
            return ReadinessDecision(
                False,
                Condition.TASKS_REQUIRED,
                ("TASKS dependency contract is incorrect, incomplete, or missing",),
            )
        if not dependencies_satisfied:
            return ReadinessDecision(
                False,
                Condition.TASK_DEPENDENCY_UNSATISFIED,
                ("a mandatory dependency TASK is not CLOSED",),
            )
        if artifact_ambiguity is not None:
            if artifact_ambiguity not in _READINESS_ARTIFACT_AMBIGUITY_CLASSIFICATIONS:
                raise WorkflowViolation(
                    f"artifact_ambiguity={artifact_ambiguity.value} is not a valid READINESS "
                    "artifact-ambiguity classification (SPEC Section 14 restricts this to "
                    "PRODUCT, ARCHITECTURE, TASKS)",
                    details={"artifact_ambiguity": artifact_ambiguity.value},
                )
            condition = RoutingPolicy.route(artifact_ambiguity)
            return ReadinessDecision(
                False,
                condition,
                (f"applicable contract is ambiguous or insufficient: {artifact_ambiguity.value}",),
            )
        return ReadinessDecision(True, None, ())
