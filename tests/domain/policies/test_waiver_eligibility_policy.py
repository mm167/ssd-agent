from __future__ import annotations

import pytest

from sdd_agent.domain.models.enums import ProblemClassification, ValidationStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult
from sdd_agent.domain.policies.waiver_eligibility import WaiverEligibilityPolicy


def _context() -> EvidenceContext:
    return EvidenceContext(task_id="T006", attempt_id="a1", candidate_id="cand-1")


def _obligation(obligation_id: str = "obl-1", *, non_waivable: bool = False) -> ValidationObligation:
    return ValidationObligation(
        obligation_id=obligation_id,
        description="d",
        execution_reference="cmd",
        required=True,
        non_waivable=non_waivable,
    )


def _result(status: ValidationStatus, obligation_id: str = "obl-1") -> ValidationResult:
    return ValidationResult(
        result_id="r1", obligation_id=obligation_id, context=_context(), status=status
    )


# -- T006-IR-001: explicit ENVIRONMENT classification is required -----------


def test_not_run_with_environment_classification_is_eligible() -> None:
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(),
        result=_result(ValidationStatus.NOT_RUN),
        cause_classification=ProblemClassification.ENVIRONMENT,
    )
    assert decision.passed


def test_not_run_with_no_classification_is_not_eligible() -> None:
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(),
        result=_result(ValidationStatus.NOT_RUN),
        cause_classification=None,
    )
    assert not decision.passed
    assert any("ENVIRONMENT" in reason for reason in decision.reasons)


@pytest.mark.parametrize(
    "classification",
    [
        ProblemClassification.CODE,
        ProblemClassification.PRODUCT,
        ProblemClassification.ARCHITECTURE,
        ProblemClassification.TASKS,
        ProblemClassification.REPOSITORY_MISMATCH,
    ],
)
def test_not_run_with_non_environment_classification_is_not_eligible(
    classification: ProblemClassification,
) -> None:
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(),
        result=_result(ValidationStatus.NOT_RUN),
        cause_classification=classification,
    )
    assert not decision.passed


def test_passed_is_not_eligible_even_with_environment_classification() -> None:
    # Reviewer probe: classification=ENVIRONMENT must not make a PASSED
    # result "eligible" for a waiver it does not need.
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(),
        result=_result(ValidationStatus.PASSED),
        cause_classification=ProblemClassification.ENVIRONMENT,
    )
    assert not decision.passed


def test_failed_is_not_eligible_even_with_environment_classification() -> None:
    # Reviewer probe: classification=ENVIRONMENT must not make a FAILED
    # result waivable (SPEC Section 22.1 is absolute).
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(),
        result=_result(ValidationStatus.FAILED),
        cause_classification=ProblemClassification.ENVIRONMENT,
    )
    assert not decision.passed
    assert any("never waivable" in reason for reason in decision.reasons)


def test_non_waivable_obligation_not_eligible_even_with_environment_classification() -> None:
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(non_waivable=True),
        result=_result(ValidationStatus.NOT_RUN),
        cause_classification=ProblemClassification.ENVIRONMENT,
    )
    assert not decision.passed
    assert any("non-waivable" in reason for reason in decision.reasons)


def test_mismatched_obligation_id_not_eligible() -> None:
    decision = WaiverEligibilityPolicy.evaluate(
        obligation=_obligation(obligation_id="obl-1"),
        result=_result(ValidationStatus.NOT_RUN, obligation_id="obl-2"),
        cause_classification=ProblemClassification.ENVIRONMENT,
    )
    assert not decision.passed


def test_cause_classification_is_a_required_argument() -> None:
    # Reviewer probe: eligibility_without_classification_input=True must no
    # longer be a valid call shape at all.
    with pytest.raises(TypeError):
        WaiverEligibilityPolicy.evaluate(  # type: ignore[call-arg]
            obligation=_obligation(), result=_result(ValidationStatus.NOT_RUN)
        )
