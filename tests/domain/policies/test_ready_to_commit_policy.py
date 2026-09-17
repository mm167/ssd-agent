from __future__ import annotations

from sdd_agent.domain.models.enums import Condition
from sdd_agent.domain.policies.decision import GateDecision
from sdd_agent.domain.policies.ready_to_commit import ReadyToCommitPolicy

_PASS = GateDecision(True, ())
_FAIL = GateDecision(False, ("some failure",))


def test_passes_when_all_inputs_are_satisfied() -> None:
    decision = ReadyToCommitPolicy.evaluate(
        ready_for_review=_PASS,
        review_gate=_PASS,
        repository_integrity_valid=True,
    )

    assert decision.passed


def test_fails_when_ready_for_review_not_applicable() -> None:
    decision = ReadyToCommitPolicy.evaluate(
        ready_for_review=_FAIL,
        review_gate=_PASS,
        repository_integrity_valid=True,
    )

    assert not decision.passed
    assert any("READY_FOR_REVIEW" in reason for reason in decision.reasons)


def test_fails_when_review_gate_not_satisfied() -> None:
    decision = ReadyToCommitPolicy.evaluate(
        ready_for_review=_PASS,
        review_gate=_FAIL,
        repository_integrity_valid=True,
    )

    assert not decision.passed
    assert any("review gate" in reason for reason in decision.reasons)


def test_fails_when_repository_integrity_invalid() -> None:
    decision = ReadyToCommitPolicy.evaluate(
        ready_for_review=_PASS,
        review_gate=_PASS,
        repository_integrity_valid=False,
    )

    assert not decision.passed


def test_fails_when_blocking_condition_present() -> None:
    decision = ReadyToCommitPolicy.evaluate(
        ready_for_review=_PASS,
        review_gate=_PASS,
        repository_integrity_valid=True,
        blocking_condition=Condition.REPOSITORY_MISMATCH,
    )

    assert not decision.passed
