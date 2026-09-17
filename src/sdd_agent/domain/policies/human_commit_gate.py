"""`HumanCommitGatePolicy` (SPEC Section 35.1; PLAN Section 55).

Entry into the Human Commit Gate is authorized only for the exact current
candidate with an applicable READY_TO_COMMIT (SPEC INV-33). This policy does
not capture the human's decision itself -- that interaction belongs to T012's
Human Commit Gate integration; this module only decides whether entry is
currently authorized.
"""

from __future__ import annotations

from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.policies.decision import GateDecision


class HumanCommitGatePolicy:
    """Deterministic Human Commit Gate entry precondition (SPEC Section 35.1)."""

    @staticmethod
    def may_enter(
        *,
        ready_to_commit: GateDecision,
        ready_to_commit_context: EvidenceContext,
        current_context: EvidenceContext,
    ) -> GateDecision:
        reasons: list[str] = []
        if not ready_to_commit.passed:
            reasons.append("READY_TO_COMMIT not applicable")
        if not ready_to_commit_context.applies_to(current_context):
            reasons.append("READY_TO_COMMIT does not apply to the current candidate")
        return GateDecision(passed=not reasons, reasons=tuple(reasons))
