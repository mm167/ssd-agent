"""`WaiverEligibilityPolicy` (TASKS T006 Scope: "Waiver request and approval
applicability"; SPEC Sections 22.1-22.2, 22.13; PLAN Sections 35-36).

Decides whether a waiver may even be *requested/granted* for a given
`ValidationObligation` + its `ValidationResult`, before any human decision
exists. This is distinct from
`sdd_agent.domain.policies.ready_for_review.ReadyForReviewPolicy`'s internal
`_applicable_waiver`, which decides whether an *already-granted*
`ValidationWaiver` still satisfies a current gate for stale/mismatched
evidence -- that check belongs to T005 and is untouched here.

SPEC Section 22.1 ("FAILED Is Never Waivable"), the NOT_RUN-only half of
Section 22.2 ("Waiver Eligibility"), and Section 22.13 (a contract may
declare an obligation non-waivable) are enforced as the eligibility
precondition.

T006-IR-001 correction: SPEC Section 22.2 also requires "the reason has been
explicitly classified: ENVIRONMENT" -- eligibility must never be computed
from `obligation`/`result` alone, since neither carries a cause
classification. `cause_classification` is therefore a required keyword
argument using this codebase's *existing* general classification model,
`sdd_agent.domain.models.enums.ProblemClassification` (SPEC Section 7; PLAN
Section 42) -- the same enum SPEC Section 20 already uses to classify a
validation failure's cause (CODE/ENVIRONMENT/PRODUCT/ARCHITECTURE/TASKS) --
rather than inventing a second, incompatible classification vocabulary.
Only `ProblemClassification.ENVIRONMENT` satisfies Section 22.2; `None` (not
yet classified) and every other member are treated as not-yet-eligible, not
as an implicit bypass. This is checked only *after* confirming the result is
NOT_RUN and the obligation is waivable, so a PASSED/FAILED result can never
become "eligible" merely because a classification of ENVIRONMENT happens to
be supplied for it.
"""

from __future__ import annotations

from sdd_agent.domain.models.enums import ProblemClassification, ValidationStatus
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult
from sdd_agent.domain.policies.decision import GateDecision


class WaiverEligibilityPolicy:
    """Deterministic waiver-eligibility precondition (SPEC Sections 22.1-22.2)."""

    @staticmethod
    def evaluate(
        *,
        obligation: ValidationObligation,
        result: ValidationResult,
        cause_classification: ProblemClassification | None,
    ) -> GateDecision:
        reasons: list[str] = []

        if result.obligation_id != obligation.obligation_id:
            reasons.append(
                f"result belongs to obligation {result.obligation_id!r}, "
                f"not {obligation.obligation_id!r}"
            )
        elif result.status is ValidationStatus.FAILED:
            reasons.append("FAILED validation is never waivable (SPEC Section 22.1)")
        elif result.status is ValidationStatus.PASSED:
            reasons.append("PASSED validation requires no waiver")
        elif obligation.non_waivable:
            reasons.append(f"obligation {obligation.obligation_id} is declared non-waivable")
        elif cause_classification is not ProblemClassification.ENVIRONMENT:
            classified_as = cause_classification.value if cause_classification is not None else "none"
            reasons.append(
                "NOT_RUN cause is not explicitly classified as ENVIRONMENT "
                f"(classified_as={classified_as}); SPEC Section 22.2 requires explicit "
                "ENVIRONMENT classification before waiver eligibility"
            )

        return GateDecision(passed=not reasons, reasons=tuple(reasons))
