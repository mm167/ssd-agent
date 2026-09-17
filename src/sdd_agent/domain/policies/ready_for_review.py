"""`ReadyForReviewPolicy` (SPEC Sections 21, 24, 90A-91; PLAN Section 91).

Computes whether READY_FOR_REVIEW holds from already-produced evidence: an
`ImplementationReport`, the required `ValidationObligation`s, their
`ValidationResult`s, and any `ValidationWaiver`s -- all evaluated against the
exact current candidate context. It does not execute validations (T006),
build the reviewer's context package (T008), or decide the
`ImplementationReport`'s own contents (T007/T011).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sdd_agent.domain.models.enums import Condition, ImplementationCompletionStatus, ValidationStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.implementation import ImplementationReport
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult, ValidationWaiver
from sdd_agent.domain.policies.decision import GateDecision

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


class ReadyForReviewPolicy:
    """Deterministic READY_FOR_REVIEW gate (PLAN Section 91)."""

    @staticmethod
    def evaluate(
        *,
        current_context: EvidenceContext,
        implementation_report: ImplementationReport | None,
        obligations: Sequence[ValidationObligation],
        results: Sequence[ValidationResult],
        waivers: Sequence[ValidationWaiver] = (),
        blocking_condition: Condition | None = None,
    ) -> GateDecision:
        reasons: list[str] = []

        if blocking_condition is not None:
            reasons.append(f"unresolved condition: {blocking_condition.value}")

        if implementation_report is None:
            reasons.append("no ImplementationReport for the current candidate")
        elif not implementation_report.context.applies_to(current_context):
            reasons.append("ImplementationReport does not apply to the current candidate (candidate changed)")
        elif implementation_report.completion_status is not ImplementationCompletionStatus.COMPLETED:
            reasons.append(
                "implementation completion_status="
                f"{implementation_report.completion_status.value}, expected completed"
            )

        for obligation in obligations:
            if not obligation.required:
                continue
            reasons.extend(_evaluate_required_obligation(obligation, results, waivers, current_context))

        return GateDecision(passed=not reasons, reasons=tuple(reasons))


def _evaluate_required_obligation(
    obligation: ValidationObligation,
    results: Sequence[ValidationResult],
    waivers: Sequence[ValidationWaiver],
    current_context: EvidenceContext,
) -> list[str]:
    result = _latest_applicable_result(obligation.obligation_id, results, current_context)
    if result is None:
        return [f"no applicable validation result for required obligation {obligation.obligation_id}"]

    if result.status is ValidationStatus.PASSED:
        return []

    if result.status is ValidationStatus.FAILED:
        return [f"required obligation {obligation.obligation_id} FAILED"]

    # ValidationStatus.NOT_RUN: a waiver is the only path forward, and only
    # when the obligation is not declared non-waivable (SPEC Section 22.13).
    if obligation.non_waivable:
        return [f"required obligation {obligation.obligation_id} is non-waivable but NOT_RUN"]
    if _applicable_waiver(obligation.obligation_id, result.result_id, waivers, current_context) is None:
        return [f"required obligation {obligation.obligation_id} NOT_RUN without an applicable waiver"]
    return []


def _latest_applicable_result(
    obligation_id: str,
    results: Sequence[ValidationResult],
    current_context: EvidenceContext,
) -> ValidationResult | None:
    applicable = [
        result
        for result in results
        if result.obligation_id == obligation_id and result.context.applies_to(current_context)
    ]
    if not applicable:
        return None
    return max(applicable, key=lambda result: result.completed_at or result.started_at or _EPOCH)


def _applicable_waiver(
    obligation_id: str,
    validation_result_id: str,
    waivers: Sequence[ValidationWaiver],
    current_context: EvidenceContext,
) -> ValidationWaiver | None:
    """The waiver applicable to the exact current NOT_RUN result, if any.

    A waiver is bound to the validation evidence that justified it (SPEC
    Section 22.5 "validation evidence", Section 22.9 "Evidence and Cause
    Binding"): matching `obligation_id` and `EvidenceContext` alone is not
    enough. If new validation evidence appears for the same obligation --
    e.g. the obligation is re-run and produces a new `ValidationResult` with
    a different `result_id`, even under an unchanged task/attempt/candidate
    context -- the old waiver does not automatically carry over (SPEC
    Section 22.9: "The old waiver cannot mask the new failure"; INV-29).
    """
    for waiver in waivers:
        if (
            waiver.obligation_id == obligation_id
            and waiver.validation_result_id == validation_result_id
            and waiver.context.applies_to(current_context)
        ):
            return waiver
    return None
