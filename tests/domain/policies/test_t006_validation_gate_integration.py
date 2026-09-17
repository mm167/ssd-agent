"""Integration/adversarial tests bridging T006 (ValidationRunner, obligations,
waivers) into T005's unmodified `ReadyForReviewPolicy` gate.

These prove real T006-produced `ValidationResult`s compose correctly with
T005's existing evidence-applicability rules, without T006 weakening,
duplicating, or bypassing them. Numbered `test_cross_finding_*` functions
correspond to the review's cross-finding regression probes 1-5 (probes 6-7
are covered in `tests/adapters/validation/test_subprocess_runner.py`).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sdd_agent.adapters.validation.fake import FakeValidationRunner
from sdd_agent.configuration.models import AgentRole
from sdd_agent.domain.models.enums import (
    ImplementationCompletionStatus,
    ProblemClassification,
    ValidationStatus,
    WaiverEligibleCause,
)
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.implementation import ImplementationReport
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult, ValidationWaiver
from sdd_agent.domain.policies.ready_for_review import ReadyForReviewPolicy
from sdd_agent.domain.policies.waiver_eligibility import WaiverEligibilityPolicy


def _context(candidate_id: str = "C1", attempt_id: str = "a1") -> EvidenceContext:
    return EvidenceContext(task_id="T099", attempt_id=attempt_id, candidate_id=candidate_id)


def _impl_report(context: EvidenceContext) -> ImplementationReport:
    return ImplementationReport(
        report_id="impl-1",
        context=context,
        implementation_role=AgentRole.IMPLEMENTER,
        completion_status=ImplementationCompletionStatus.COMPLETED,
        changed_paths=["x.py"],
        task_scope_summary="x",
    )


def _obligation(obligation_id: str = "O1", *, non_waivable: bool = False) -> ValidationObligation:
    return ValidationObligation(
        obligation_id=obligation_id,
        description="d",
        execution_reference="missing-cmd",
        required=True,
        non_waivable=non_waivable,
    )


def _waiver(
    *, obligation_id: str, context: EvidenceContext, validation_result_id: str
) -> ValidationWaiver:
    return ValidationWaiver(
        waiver_id=f"waiver-for-{validation_result_id}",
        obligation_id=obligation_id,
        context=context,
        cause=WaiverEligibleCause.ENVIRONMENT,
        validation_result_id=validation_result_id,
        human_decision_id="H1",
        reason="env down",
    )


def test_runner_not_run_plus_eligible_waiver_satisfies_t005_gate() -> None:
    context = _context()
    obligation = _obligation()
    result = FakeValidationRunner({"O1": ValidationStatus.NOT_RUN}).run(
        obligation, context, result_id="R1"
    )

    eligibility = WaiverEligibilityPolicy.evaluate(
        obligation=obligation, result=result, cause_classification=ProblemClassification.ENVIRONMENT
    )
    assert eligibility.passed

    waiver = _waiver(obligation_id="O1", context=context, validation_result_id=result.result_id)

    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[result],
        waivers=[waiver],
    )
    assert decision.passed


def test_runner_failed_cannot_be_waived_even_if_a_waiver_is_constructed() -> None:
    context = _context()
    obligation = _obligation()
    result = FakeValidationRunner({"O1": ValidationStatus.FAILED}).run(
        obligation, context, result_id="R1"
    )

    eligibility = WaiverEligibilityPolicy.evaluate(
        obligation=obligation, result=result, cause_classification=ProblemClassification.ENVIRONMENT
    )
    assert not eligibility.passed
    assert any("never waivable" in reason for reason in eligibility.reasons)

    waiver = _waiver(obligation_id="O1", context=context, validation_result_id=result.result_id)
    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[result],
        waivers=[waiver],
    )
    assert not decision.passed
    assert any("FAILED" in reason for reason in decision.reasons)


def test_waiver_from_another_candidate_does_not_apply() -> None:
    context = _context(candidate_id="C1")
    other_candidate_context = _context(candidate_id="C2")
    obligation = _obligation()
    result = FakeValidationRunner({"O1": ValidationStatus.NOT_RUN}).run(
        obligation, context, result_id="R1"
    )
    waiver = _waiver(
        obligation_id="O1", context=other_candidate_context, validation_result_id=result.result_id
    )

    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[result],
        waivers=[waiver],
    )
    assert not decision.passed


# -- cross-finding regression probes (post T006-IR-001/002/003 fixes) -------


def _timed_result(
    *, result_id: str, context: EvidenceContext, status: ValidationStatus, when: datetime
) -> ValidationResult:
    return ValidationResult(
        result_id=result_id,
        obligation_id="O1",
        context=context,
        status=status,
        completed_at=when,
    )


def test_cross_finding_1_not_run_no_environment_classification_denied() -> None:
    context = _context()
    obligation = _obligation()
    result = FakeValidationRunner({"O1": ValidationStatus.NOT_RUN}).run(
        obligation, context, result_id="R1"
    )

    eligibility = WaiverEligibilityPolicy.evaluate(
        obligation=obligation, result=result, cause_classification=None
    )
    assert not eligibility.passed


def test_cross_finding_2_not_run_environment_current_result_bound_waiver_eligible() -> None:
    context = _context()
    obligation = _obligation()
    result = FakeValidationRunner({"O1": ValidationStatus.NOT_RUN}).run(
        obligation, context, result_id="R1"
    )

    eligibility = WaiverEligibilityPolicy.evaluate(
        obligation=obligation, result=result, cause_classification=ProblemClassification.ENVIRONMENT
    )
    assert eligibility.passed

    waiver = _waiver(obligation_id="O1", context=context, validation_result_id=result.result_id)
    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[result],
        waivers=[waiver],
    )
    assert decision.passed


def test_cross_finding_3_waiver_bound_to_historical_result_does_not_satisfy_current_gate() -> None:
    context = _context()
    obligation = _obligation()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    r1_historical = _timed_result(
        result_id="R1", context=context, status=ValidationStatus.NOT_RUN, when=base
    )
    r2_current = _timed_result(
        result_id="R2",
        context=context,
        status=ValidationStatus.NOT_RUN,
        when=base + timedelta(hours=1),
    )
    waiver_on_r1 = _waiver(obligation_id="O1", context=context, validation_result_id="R1")

    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[r1_historical, r2_current],
        waivers=[waiver_on_r1],
    )
    assert not decision.passed


def test_cross_finding_4_waiver_bound_to_actual_current_result_satisfies_gate() -> None:
    context = _context()
    obligation = _obligation()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    r1_historical = _timed_result(
        result_id="R1", context=context, status=ValidationStatus.NOT_RUN, when=base
    )
    r2_current = _timed_result(
        result_id="R2",
        context=context,
        status=ValidationStatus.NOT_RUN,
        when=base + timedelta(hours=1),
    )
    waiver_on_r2 = _waiver(obligation_id="O1", context=context, validation_result_id="R2")

    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[r1_historical, r2_current],
        waivers=[waiver_on_r2],
    )
    assert decision.passed


def test_cross_finding_5_non_waivable_obligation_denied_even_with_environment_and_waiver() -> None:
    context = _context()
    obligation = _obligation(non_waivable=True)
    result = FakeValidationRunner({"O1": ValidationStatus.NOT_RUN}).run(
        obligation, context, result_id="R1"
    )

    eligibility = WaiverEligibilityPolicy.evaluate(
        obligation=obligation, result=result, cause_classification=ProblemClassification.ENVIRONMENT
    )
    assert not eligibility.passed

    waiver = _waiver(obligation_id="O1", context=context, validation_result_id=result.result_id)
    decision = ReadyForReviewPolicy.evaluate(
        current_context=context,
        implementation_report=_impl_report(context),
        obligations=[obligation],
        results=[result],
        waivers=[waiver],
    )
    assert not decision.passed
    assert any("non-waivable" in reason for reason in decision.reasons)
