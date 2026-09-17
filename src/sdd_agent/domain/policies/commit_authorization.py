"""`CommitAuthorizationPolicy` (SPEC Sections 34-37, INV-34, INV-35; PLAN
Section 93).

``COMMIT_ALLOWED(candidate) = READY_TO_COMMIT(candidate).applicable AND
HUMAN_APPROVAL(candidate).applicable``

Both proofs must refer to the exact same current candidate (SPEC Section 37).
This policy deliberately does not interpret `HumanDecision.choice` or decide
what counts as an "approval" -- that semantic judgment belongs to T012, which
owns Human Decisions and the Commit Approval Gate. T005 only accepts the
*context* of an already-determined applicable commit approval (or `None` if
none exists) and performs the exact-candidate identity check both SPEC
Section 37 forbidden combinations hinge on.
"""

from __future__ import annotations

from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.policies.decision import GateDecision


class CommitAuthorizationPolicy:
    """Deterministic COMMIT authorization (SPEC Section 37; PLAN Section 93)."""

    @staticmethod
    def authorize(
        *,
        ready_to_commit: GateDecision,
        ready_to_commit_context: EvidenceContext,
        human_approval_context: EvidenceContext | None,
        current_context: EvidenceContext,
    ) -> GateDecision:
        reasons: list[str] = []

        if not ready_to_commit.passed:
            reasons.append("READY_TO_COMMIT not applicable")
        elif not ready_to_commit_context.applies_to(current_context):
            reasons.append("READY_TO_COMMIT does not apply to the current candidate")

        if human_approval_context is None:
            reasons.append("human approval missing")
        elif not human_approval_context.applies_to(current_context):
            reasons.append("human approval does not apply to the current candidate")

        return GateDecision(passed=not reasons, reasons=tuple(reasons))
