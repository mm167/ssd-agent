from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import EvidenceContext, HumanDecision, HumanDecisionType


def _context() -> EvidenceContext:
    return EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")


def test_human_decision_minimal() -> None:
    decision = HumanDecision(
        decision_id="d1",
        decision_type=HumanDecisionType.COMMIT_APPROVAL,
        context=_context(),
        choice="approve",
    )

    assert decision.decision_type is HumanDecisionType.COMMIT_APPROVAL


def test_rejects_unsupported_decision_type() -> None:
    with pytest.raises(ValidationError):
        HumanDecision(
            decision_id="d1",
            decision_type="not-a-real-type",
            context=_context(),
            choice="approve",
        )


def test_rejects_empty_choice() -> None:
    with pytest.raises(ValidationError):
        HumanDecision(
            decision_id="d1",
            decision_type=HumanDecisionType.COMMIT_APPROVAL,
            context=_context(),
            choice="",
        )


def test_requires_context() -> None:
    with pytest.raises(ValidationError):
        HumanDecision(  # type: ignore[call-arg]
            decision_id="d1",
            decision_type=HumanDecisionType.COMMIT_APPROVAL,
            choice="approve",
        )


def test_is_frozen() -> None:
    decision = HumanDecision(
        decision_id="d1",
        decision_type=HumanDecisionType.COMMIT_APPROVAL,
        context=_context(),
        choice="approve",
    )

    with pytest.raises(ValidationError):
        decision.choice = "refuse"  # type: ignore[misc]


def test_has_no_stored_applicability_field() -> None:
    decision = HumanDecision(
        decision_id="d1",
        decision_type=HumanDecisionType.COMMIT_APPROVAL,
        context=_context(),
        choice="approve",
    )

    assert not hasattr(decision, "applicability")
    assert not hasattr(decision, "is_applicable")
