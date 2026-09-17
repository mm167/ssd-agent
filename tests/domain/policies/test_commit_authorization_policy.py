from __future__ import annotations

from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.policies.commit_authorization import CommitAuthorizationPolicy
from sdd_agent.domain.policies.decision import GateDecision

_PASS = GateDecision(True, ())
_FAIL = GateDecision(False, ("not ready",))


def _context(candidate_id: str) -> EvidenceContext:
    return EvidenceContext(task_id="T005", attempt_id="a1", candidate_id=candidate_id)


def test_authorized_with_both_applicable_proofs_for_same_candidate() -> None:
    decision = CommitAuthorizationPolicy.authorize(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-1"),
        human_approval_context=_context("cand-1"),
        current_context=_context("cand-1"),
    )

    assert decision.passed


def test_forbidden_without_human_approval() -> None:
    # SPEC US-27 / INV-16: READY_TO_COMMIT alone cannot authorize COMMIT.
    decision = CommitAuthorizationPolicy.authorize(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-1"),
        human_approval_context=None,
        current_context=_context("cand-1"),
    )

    assert not decision.passed


def test_forbidden_without_ready_to_commit() -> None:
    # SPEC US-26: human approval alone cannot authorize COMMIT.
    decision = CommitAuthorizationPolicy.authorize(
        ready_to_commit=_FAIL,
        ready_to_commit_context=_context("cand-1"),
        human_approval_context=_context("cand-1"),
        current_context=_context("cand-1"),
    )

    assert not decision.passed


def test_forbidden_when_ready_to_commit_and_approval_refer_to_different_candidates() -> None:
    # SPEC US-28: READY_TO_COMMIT(A) + approval(B) -> forbidden for both.
    decision = CommitAuthorizationPolicy.authorize(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-a"),
        human_approval_context=_context("cand-b"),
        current_context=_context("cand-a"),
    )

    assert not decision.passed


def test_forbidden_when_ready_to_commit_is_stale_but_approval_is_current() -> None:
    decision = CommitAuthorizationPolicy.authorize(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-old"),
        human_approval_context=_context("cand-new"),
        current_context=_context("cand-new"),
    )

    assert not decision.passed


def test_forbidden_when_approval_is_stale_but_ready_to_commit_is_current() -> None:
    decision = CommitAuthorizationPolicy.authorize(
        ready_to_commit=_PASS,
        ready_to_commit_context=_context("cand-new"),
        human_approval_context=_context("cand-old"),
        current_context=_context("cand-new"),
    )

    assert not decision.passed
