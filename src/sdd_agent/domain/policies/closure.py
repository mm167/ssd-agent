"""`ClosurePolicy` (SPEC Section 46; PLAN Section 95).

CLOSED is computed from current applicable evidence; it is never manually
assignable (SPEC Section 46, PLAN Section 95) -- there is no `mark_closed()`
in this codebase, only this deterministic evaluation. Hosted CI GREEN for the
current expected commit is non-waivable (SPEC Section 22.14, INV-18, INV-19)
and is checked by identity against `expected_commit`, not merely by
requiring *some* GREEN result to exist somewhere.

This policy does not fetch CI evidence, verify remote state, or perform
Git/commit/push operations -- those facts are supplied by the caller
(T013/T014/T015/T016).
"""

from __future__ import annotations

from sdd_agent.domain.models.ci import CIResult
from sdd_agent.domain.models.enums import CIStatus
from sdd_agent.domain.policies.decision import GateDecision


class ClosurePolicy:
    """Deterministic CLOSED evaluation (SPEC Section 46; PLAN Section 95)."""

    @staticmethod
    def evaluate(
        *,
        review_gate_satisfied: bool,
        ready_to_commit_applicable: bool,
        human_commit_approval_applicable: bool,
        commit_created: bool,
        pushed: bool,
        remote_target_verified: bool,
        repository_mismatch: bool,
        expected_commit: str,
        ci_result: CIResult | None,
    ) -> GateDecision:
        reasons: list[str] = []

        if not review_gate_satisfied:
            reasons.append("review gate not satisfied")
        if not ready_to_commit_applicable:
            reasons.append("READY_TO_COMMIT not applicable to the committed candidate lineage")
        if not human_commit_approval_applicable:
            reasons.append("human commit approval not applicable to the committed candidate")
        if not commit_created:
            reasons.append("current expected candidate is not committed")
        if not pushed:
            reasons.append("current expected commit is not pushed")
        if not remote_target_verified:
            reasons.append("expected remote target does not correspond to the current expected pushed state")
        if repository_mismatch:
            reasons.append("unresolved repository mismatch affecting closure")

        if ci_result is None:
            reasons.append("no hosted CI evidence for the current expected commit")
        elif ci_result.expected_commit != expected_commit:
            reasons.append("hosted CI evidence applies to an obsolete expected commit")
        elif ci_result.status is not CIStatus.GREEN:
            reasons.append(f"hosted CI status={ci_result.status.value}, GREEN required (non-waivable)")

        return GateDecision(passed=not reasons, reasons=tuple(reasons))
