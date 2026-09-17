from __future__ import annotations

from datetime import datetime, timezone

from sdd_agent.configuration.models import AgentRole
from sdd_agent.domain.models.enums import Condition, ImplementationCompletionStatus, ValidationStatus, WaiverEligibleCause
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.implementation import ImplementationReport
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult, ValidationWaiver
from sdd_agent.domain.policies.ready_for_review import ReadyForReviewPolicy


def _context(candidate_id: str = "cand-1") -> EvidenceContext:
    return EvidenceContext(task_id="T005", attempt_id="a1", candidate_id=candidate_id)


def _implementation_report(candidate_id: str = "cand-1", status=ImplementationCompletionStatus.COMPLETED) -> ImplementationReport:
    return ImplementationReport(
        report_id="impl-1",
        context=_context(candidate_id),
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=status,
        task_scope_summary="implemented T005 policies",
    )


def _obligation(obligation_id: str = "pytest", required: bool = True, non_waivable: bool = False) -> ValidationObligation:
    return ValidationObligation(
        obligation_id=obligation_id,
        description="pytest suite",
        execution_reference="uv run pytest",
        required=required,
        non_waivable=non_waivable,
    )


def _result(
    obligation_id: str,
    status: ValidationStatus,
    candidate_id: str = "cand-1",
) -> ValidationResult:
    return ValidationResult(
        result_id=f"{obligation_id}-result",
        obligation_id=obligation_id,
        context=_context(candidate_id),
        status=status,
        completed_at=datetime.now(timezone.utc),
    )


def _waiver(obligation_id: str, candidate_id: str = "cand-1") -> ValidationWaiver:
    return ValidationWaiver(
        waiver_id=f"{obligation_id}-waiver",
        obligation_id=obligation_id,
        context=_context(candidate_id),
        cause=WaiverEligibleCause.ENVIRONMENT,
        validation_result_id=f"{obligation_id}-result",
        human_decision_id="decision-1",
        reason="CI runner unavailable",
    )


def test_ready_when_implementation_completed_and_validation_passed() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.PASSED)],
    )

    assert decision.passed
    assert decision.reasons == ()


def test_not_ready_without_implementation_report() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=None,
        obligations=[],
        results=[],
    )

    assert not decision.passed
    assert any("ImplementationReport" in reason for reason in decision.reasons)


def test_not_ready_when_implementation_report_is_for_a_different_candidate() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context("cand-2"),
        implementation_report=_implementation_report("cand-1"),
        obligations=[],
        results=[],
    )

    assert not decision.passed
    assert any("does not apply" in reason for reason in decision.reasons)


def test_not_ready_when_implementation_incomplete() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(status=ImplementationCompletionStatus.INCOMPLETE),
        obligations=[],
        results=[],
    )

    assert not decision.passed


def test_not_ready_when_required_validation_failed() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.FAILED)],
    )

    assert not decision.passed
    assert any("FAILED" in reason for reason in decision.reasons)


def test_not_ready_when_required_validation_missing() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[],
    )

    assert not decision.passed
    assert any("no applicable validation result" in reason for reason in decision.reasons)


def test_not_required_obligation_without_result_does_not_block() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation("optional-lint", required=False)],
        results=[],
    )

    assert decision.passed


def test_not_run_with_applicable_waiver_passes() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.NOT_RUN)],
        waivers=[_waiver("pytest")],
    )

    assert decision.passed


def test_not_run_without_waiver_blocks() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.NOT_RUN)],
        waivers=[],
    )

    assert not decision.passed
    assert any("without an applicable waiver" in reason for reason in decision.reasons)


def test_waiver_for_a_different_candidate_does_not_apply() -> None:
    # SPEC Section 22.7 / US-33: a waiver bound to Candidate A does not
    # automatically apply once the candidate changes to B.
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context("cand-2"),
        implementation_report=_implementation_report("cand-2"),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.NOT_RUN, candidate_id="cand-2")],
        waivers=[_waiver("pytest", candidate_id="cand-1")],
    )

    assert not decision.passed
    assert any("without an applicable waiver" in reason for reason in decision.reasons)


def test_non_waivable_obligation_not_run_blocks_even_with_waiver() -> None:
    # SPEC Section 22.13: a non-waivable validation must achieve its actual
    # required result; a waiver cannot rescue it.
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation(non_waivable=True)],
        results=[_result("pytest", ValidationStatus.NOT_RUN)],
        waivers=[_waiver("pytest")],
    )

    assert not decision.passed
    assert any("non-waivable" in reason for reason in decision.reasons)


def test_stale_result_for_previous_candidate_does_not_satisfy_current_candidate() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context("cand-2"),
        implementation_report=_implementation_report("cand-2"),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.PASSED, candidate_id="cand-1")],
    )

    assert not decision.passed


def test_unresolved_blocking_condition_prevents_review() -> None:
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.PASSED)],
        blocking_condition=Condition.ENVIRONMENT_BLOCKED,
    )

    assert not decision.passed


def test_waiver_bound_to_the_current_validation_result_id_applies() -> None:
    # T005-IR-001 case A: waiver.validation_result_id matches the current
    # selected NOT_RUN result's result_id, and every other applicability
    # dimension (obligation, EvidenceContext) is valid.
    result = _result("pytest", ValidationStatus.NOT_RUN)
    waiver = _waiver("pytest")
    assert waiver.validation_result_id == result.result_id  # fixture sanity check

    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[result],
        waivers=[waiver],
    )

    assert decision.passed


def test_waiver_bound_to_a_different_validation_result_id_does_not_apply() -> None:
    # T005-IR-001 case B: same task/attempt/candidate/obligation, but the
    # waiver is bound to a different (older) ValidationResult.result_id than
    # the one currently selected. READY_FOR_REVIEW must not incorrectly pass.
    current_result = ValidationResult(
        result_id="new-not-run",
        obligation_id="pytest",
        context=_context(),
        status=ValidationStatus.NOT_RUN,
    )
    stale_waiver = ValidationWaiver(
        waiver_id="waiver-1",
        obligation_id="pytest",
        context=_context(),
        cause=WaiverEligibleCause.ENVIRONMENT,
        validation_result_id="old-not-run",
        human_decision_id="decision-1",
        reason="previously waived evidence",
    )

    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[current_result],
        waivers=[stale_waiver],
    )

    assert not decision.passed
    assert any("without an applicable waiver" in reason for reason in decision.reasons)


def test_historical_waiver_does_not_authorize_replacement_evidence_with_unchanged_context() -> None:
    # T005-IR-001 case C: SPEC Section 22.9 "Evidence and Cause Binding" -- an
    # unchanged EvidenceContext (same task/attempt/candidate) is not enough:
    # once new validation evidence (a new result_id) appears for the same
    # obligation, the old waiver cannot mask/authorize it.
    replacement_result = ValidationResult(
        result_id="run-2",
        obligation_id="pytest",
        context=_context(),
        status=ValidationStatus.NOT_RUN,
    )
    waiver_for_prior_run = ValidationWaiver(
        waiver_id="waiver-1",
        obligation_id="pytest",
        context=_context(),
        cause=WaiverEligibleCause.ENVIRONMENT,
        validation_result_id="run-1",
        human_decision_id="decision-1",
        reason="CI runner unavailable at the time",
    )

    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[replacement_result],
        waivers=[waiver_for_prior_run],
    )

    assert not decision.passed


def test_valid_waiver_behavior_remains_green() -> None:
    # T005-IR-001 case D: pre-existing valid-waiver behavior is unaffected.
    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[_result("pytest", ValidationStatus.NOT_RUN)],
        waivers=[_waiver("pytest")],
    )

    assert decision.passed


def test_latest_applicable_result_wins_when_multiple_exist() -> None:
    stale = ValidationResult(
        result_id="pytest-result-1",
        obligation_id="pytest",
        context=_context(),
        status=ValidationStatus.FAILED,
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    fresh = ValidationResult(
        result_id="pytest-result-2",
        obligation_id="pytest",
        context=_context(),
        status=ValidationStatus.PASSED,
        completed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    decision = ReadyForReviewPolicy.evaluate(
        current_context=_context(),
        implementation_report=_implementation_report(),
        obligations=[_obligation()],
        results=[stale, fresh],
    )

    assert decision.passed
