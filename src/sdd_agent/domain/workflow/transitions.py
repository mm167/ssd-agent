"""Phase transition authorization (PLAN Section 9.1; SPEC Section 66).

This module authorizes *structural* phase legality only: whether a
transition could ever be valid in the conceptual lifecycle graph (SPEC
Section 66), independent of whether current evidence justifies performing it
right now. Evidence sufficiency for a specific transition is a separate
concern owned by the relevant gate policy (`sdd_agent.domain.policies`); an
Orchestrator (T011/T017) must satisfy both before performing a transition.

There is no bypass parameter. An unauthorized transition always raises
`WorkflowViolation` rather than being silently coerced into an allowed one.
"""

from __future__ import annotations

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.domain.models.enums import Phase

TERMINAL_PHASES: frozenset[Phase] = frozenset({Phase.CLOSED, Phase.ABANDONED})
"""Phases with no outgoing transition at all (public: reused by
`sdd_agent.domain.workflow.next_action` to bound its Phase/Condition
compatibility matrix without duplicating this fact).
"""

_FORWARD_TRANSITIONS: dict[Phase, frozenset[Phase]] = {
    Phase.READINESS: frozenset({Phase.IMPLEMENTATION}),
    Phase.IMPLEMENTATION: frozenset({Phase.VALIDATION}),
    Phase.VALIDATION: frozenset({Phase.REVIEW, Phase.RE_REVIEW}),
    Phase.REVIEW: frozenset({Phase.FIX, Phase.READY_TO_COMMIT}),
    Phase.FIX: frozenset({Phase.VALIDATION}),
    Phase.RE_REVIEW: frozenset({Phase.FIX, Phase.READY_TO_COMMIT}),
    Phase.READY_TO_COMMIT: frozenset({Phase.COMMIT, Phase.FIX}),
    Phase.COMMIT: frozenset({Phase.PUSH}),
    Phase.PUSH: frozenset({Phase.CI}),
    Phase.CI: frozenset({Phase.CLOSED, Phase.FIX}),
}
"""Forward-progress edges specific to each phase (SPEC Section 66 diagram).

`VALIDATION` may reach either `REVIEW` (first pass) or `RE_REVIEW` (after
FIX); which one applies to a specific transition is decided by the caller,
not by this structural map. `FIX` intentionally omits `RE_REVIEW`: SPEC
Section 32 mandates FIX always returns through VALIDATION first -- there is
no direct FIX -> RE_REVIEW edge (this is also why `IMPLEMENTATION ->
REVIEW` is absent: SPEC Section 18 forbids skipping VALIDATION).
"""

ARTIFACT_RETURN_ELIGIBLE_PHASES: frozenset[Phase] = frozenset(
    {
        Phase.IMPLEMENTATION,
        Phase.VALIDATION,
        Phase.REVIEW,
        Phase.RE_REVIEW,
        Phase.READY_TO_COMMIT,
        Phase.CI,
    }
)
"""Phases from which an approved artifact change returns the workflow through
READINESS (SPEC Sections 16, 20, 29, 35.6, 41-44; PLAN Section 90): a
resolved PRODUCT/ARCHITECTURE/TASKS ambiguity discovered during
IMPLEMENTATION, VALIDATION, REVIEW/RE_REVIEW, a human-requested change at
READY_TO_COMMIT, or CI failure classified as an artifact problem. COMMIT and
PUSH are short orchestrated Git actions (T013) with no described artifact-
ambiguity discovery point, so they are excluded.

Public: reused as-is by `sdd_agent.domain.workflow.next_action`'s Phase/
Condition compatibility matrix, so the set of phases from which SPEC_REQUIRED/
PLAN_REQUIRED/TASKS_REQUIRED are valid is defined exactly once.
"""


def valid_targets(current: Phase) -> frozenset[Phase]:
    """Every phase a transition from `current` could ever legally reach.

    Every non-terminal phase can always additionally move to `ABANDONED`: the
    human may abandon an active Attempt at any time (SPEC Section 58).
    """
    if current in TERMINAL_PHASES:
        return frozenset()
    targets = _FORWARD_TRANSITIONS.get(current, frozenset()) | {Phase.ABANDONED}
    if current in ARTIFACT_RETURN_ELIGIBLE_PHASES:
        targets = targets | {Phase.READINESS}
    return targets


def authorize_transition(current: Phase, target: Phase) -> None:
    """Raise `WorkflowViolation` unless `current -> target` is structurally valid.

    This never returns a "soft" rejection value a caller might accidentally
    ignore: an invalid transition is always an explicit error.
    """
    if target not in valid_targets(current):
        raise WorkflowViolation(
            f"phase transition {current.value} -> {target.value} is not authorized",
            details={"current_phase": current.value, "target_phase": target.value},
        )
