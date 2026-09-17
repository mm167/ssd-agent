"""`ReviewGatePolicy` (SPEC Sections 25-30; PLAN Section 40).

The deterministic review gate: `BLOCKER == 0 AND IMPORTANT == 0`, evaluated
only for a `ReviewReport` that still applies to the current candidate (SPEC
INV-12, INV-13). Reviewer prose such as "looks good" has no authority here
(SPEC Section 30) -- only the structured `Finding.severity` counts do.
"""

from __future__ import annotations

from sdd_agent.domain.models.enums import FindingSeverity
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.review import ReviewReport
from sdd_agent.domain.policies.decision import GateDecision


class ReviewGatePolicy:
    """Deterministic review gate (SPEC Section 30; PLAN Section 40)."""

    @staticmethod
    def evaluate(review: ReviewReport, current_context: EvidenceContext) -> GateDecision:
        if not review.context.applies_to(current_context):
            return GateDecision(False, ("review does not apply to the current candidate (candidate changed)",))

        blocker_count = sum(1 for finding in review.findings if finding.severity is FindingSeverity.BLOCKER)
        important_count = sum(1 for finding in review.findings if finding.severity is FindingSeverity.IMPORTANT)
        if blocker_count or important_count:
            return GateDecision(False, (f"BLOCKER={blocker_count}", f"IMPORTANT={important_count}"))
        return GateDecision(True, ())
