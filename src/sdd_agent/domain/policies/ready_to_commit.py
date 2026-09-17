"""`ReadyToCommitPolicy` (SPEC Section 34; PLAN Section 92).

Composes the already-evaluated READY_FOR_REVIEW and review-gate decisions
plus repository integrity into the candidate-specific READY_TO_COMMIT gate.
It does not recompute either sub-decision itself: callers (T011) evaluate
`ReadyForReviewPolicy`/`ReviewGatePolicy` against the current context and
pass the results in, keeping each gate independently testable and avoiding
duplicated evidence-matching logic.
"""

from __future__ import annotations

from sdd_agent.domain.models.enums import Condition
from sdd_agent.domain.policies.decision import GateDecision


class ReadyToCommitPolicy:
    """Deterministic READY_TO_COMMIT gate (PLAN Section 92)."""

    @staticmethod
    def evaluate(
        *,
        ready_for_review: GateDecision,
        review_gate: GateDecision,
        repository_integrity_valid: bool,
        blocking_condition: Condition | None = None,
    ) -> GateDecision:
        reasons: list[str] = []
        if blocking_condition is not None:
            reasons.append(f"unresolved condition: {blocking_condition.value}")
        if not ready_for_review.passed:
            reasons.append("READY_FOR_REVIEW not applicable")
            reasons.extend(ready_for_review.reasons)
        if not review_gate.passed:
            reasons.append("review gate not satisfied")
            reasons.extend(review_gate.reasons)
        if not repository_integrity_valid:
            reasons.append("repository integrity invalid")
        return GateDecision(passed=not reasons, reasons=tuple(reasons))
