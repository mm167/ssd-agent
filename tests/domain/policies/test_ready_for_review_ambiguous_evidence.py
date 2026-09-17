"""T006-IR-002 regression: identifying the *current* `ValidationResult` for
an obligation must never depend on caller-supplied list order, and must
never fall back to a permissive default (the old `_EPOCH` behavior) when
ordering cannot be determined.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sdd_agent.configuration.models import AgentRole
from sdd_agent.domain.models.enums import ImplementationCompletionStatus, ValidationStatus, WaiverEligibleCause
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.implementation import ImplementationReport
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult, ValidationWaiver
from sdd_agent.domain.policies.ready_for_review import ReadyForReviewPolicy

_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> EvidenceContext:
    return EvidenceContext(task_id="T005", attempt_id="a1", candidate_id="cand-1")


def _impl_report() -> ImplementationReport:
    return ImplementationReport(
        report_id="impl-1",
        context=_context(),
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=ImplementationCompletionStatus.COMPLETED,
        task_scope_summary="x",
    )


def _obligation() -> ValidationObligation:
    return ValidationObligation(
        obligation_id="O1", description="d", execution_reference="cmd", required=True
    )


def _result(result_id: str, status: ValidationStatus, completed_at: datetime | None) -> ValidationResult:
    return ValidationResult(
        result_id=result_id,
        obligation_id="O1",
        context=_context(),
        status=status,
        completed_at=completed_at,
    )


def _waiver(validation_result_id: str) -> ValidationWaiver:
    return ValidationWaiver(
        waiver_id=f"waiver-{validation_result_id}",
        obligation_id="O1",
        context=_context(),
        cause=WaiverEligibleCause.ENVIRONMENT,
        validation_result_id=validation_result_id,
        human_decision_id="H1",
        reason="env down",
    )


def _evaluate(results: list[ValidationResult], waivers: list[ValidationWaiver]) -> bool:
    return ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_impl_report(),
        obligations=[_obligation()],
        results=results,
        waivers=waivers,
    ).passed


def test_reviewer_probe_untimed_duplicate_not_run_results_reject_stale_waiver_either_order() -> None:
    r1 = _result("R1", ValidationStatus.NOT_RUN, completed_at=None)
    r2 = _result("R2", ValidationStatus.NOT_RUN, completed_at=None)
    waiver_on_r1 = _waiver("R1")

    # Exact reviewer probe: both untimed, waiver bound to R1. Neither list
    # order may resolve to "R1 is current" (the old _EPOCH fallback did).
    assert _evaluate([r1, r2], [waiver_on_r1]) is False
    assert _evaluate([r2, r1], [waiver_on_r1]) is False


def test_timed_results_pick_the_same_current_result_regardless_of_list_order() -> None:
    stale = _result("R1", ValidationStatus.FAILED, completed_at=_BASE)
    fresh = _result("R2", ValidationStatus.PASSED, completed_at=_BASE + timedelta(hours=1))

    assert _evaluate([stale, fresh], []) is True
    assert _evaluate([fresh, stale], []) is True


def test_timed_results_with_waiver_bound_to_actual_current_result_passes_either_order() -> None:
    stale = _result("R1", ValidationStatus.NOT_RUN, completed_at=_BASE)
    current = _result("R2", ValidationStatus.NOT_RUN, completed_at=_BASE + timedelta(hours=1))
    waiver_on_current = _waiver("R2")

    assert _evaluate([stale, current], [waiver_on_current]) is True
    assert _evaluate([current, stale], [waiver_on_current]) is True


def test_exact_tie_at_maximum_timestamp_is_ambiguous_not_first_in_list() -> None:
    tied_a = _result("R1", ValidationStatus.PASSED, completed_at=_BASE)
    tied_b = _result("R2", ValidationStatus.FAILED, completed_at=_BASE)

    # If list order silently broke the tie, [tied_a, tied_b] would read as
    # PASSED (gate passes) while [tied_b, tied_a] would read as FAILED (gate
    # fails). Both must instead be treated as ambiguous -> gate fails either way.
    assert _evaluate([tied_a, tied_b], []) is False
    assert _evaluate([tied_b, tied_a], []) is False


def test_one_untimed_result_among_timed_results_is_ambiguous() -> None:
    timed = _result("R1", ValidationStatus.PASSED, completed_at=_BASE)
    untimed = _result("R2", ValidationStatus.PASSED, completed_at=None)

    # Whether the untimed result happened before or after `timed` cannot be
    # determined, so this must not silently resolve to either one.
    assert _evaluate([timed, untimed], []) is False
    assert _evaluate([untimed, timed], []) is False


def test_single_untimed_result_is_not_ambiguous() -> None:
    # A single applicable result is never "ambiguous" merely for lacking a
    # timestamp -- there is nothing to order it against.
    only = _result("R1", ValidationStatus.PASSED, completed_at=None)
    assert _evaluate([only], []) is True
