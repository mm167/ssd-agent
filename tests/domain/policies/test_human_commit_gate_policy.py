from __future__ import annotations

from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.policies.decision import GateDecision
from sdd_agent.domain.policies.human_commit_gate import HumanCommitGatePolicy

_PASS = GateDecision(True, ())
_FAIL = GateDecision(False, ("not ready",))


def _context(candidate_id: str) -> EvidenceContext:
    return EvidenceContext(task_id="T005", attempt_id="a1", candidate_id=candidate_id)


def test_entry_allowed_with_applicable_ready_to_commit() -> None:
    decision = HumanCommitGatePolicy.may_enter(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-1"),
        current_context=_context("cand-1"),
    )

    assert decision.passed


def test_entry_forbidden_without_ready_to_commit() -> None:
    # SPEC US-23: Human Commit Gate entry is forbidden when READY_TO_COMMIT
    # is absent for the exact current candidate.
    decision = HumanCommitGatePolicy.may_enter(
        ready_to_commit=_FAIL,
        ready_to_commit_context=_context("cand-1"),
        current_context=_context("cand-1"),
    )

    assert not decision.passed


def test_entry_forbidden_when_ready_to_commit_is_for_a_different_candidate() -> None:
    # SPEC Section 34: READY_TO_COMMIT is stale once the candidate changed.
    decision = HumanCommitGatePolicy.may_enter(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-1"),
        current_context=_context("cand-2"),
    )

    assert not decision.passed
