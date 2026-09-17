from __future__ import annotations

from sdd_agent.domain.models.ci import CIResult
from sdd_agent.domain.models.enums import CIStatus
from sdd_agent.domain.policies.closure import ClosurePolicy

_ALL_TRUE_KWARGS = dict(
    review_gate_satisfied=True,
    ready_to_commit_applicable=True,
    human_commit_approval_applicable=True,
    commit_created=True,
    pushed=True,
    remote_target_verified=True,
    repository_mismatch=False,
)


def _ci_result(expected_commit: str, status: CIStatus) -> CIResult:
    return CIResult(
        result_id="ci-1",
        task_id="T005",
        attempt_id="a1",
        expected_commit=expected_commit,
        status=status,
    )


def test_closed_when_every_condition_satisfied() -> None:
    decision = ClosurePolicy.evaluate(
        **_ALL_TRUE_KWARGS,
        expected_commit="abc123",
        ci_result=_ci_result("abc123", CIStatus.GREEN),
    )

    assert decision.passed


def test_not_closed_without_ci_evidence() -> None:
    decision = ClosurePolicy.evaluate(
        **_ALL_TRUE_KWARGS,
        expected_commit="abc123",
        ci_result=None,
    )

    assert not decision.passed


def test_not_closed_when_ci_green_for_a_different_commit() -> None:
    # SPEC INV-19 / Section 45: CI GREEN for commit A cannot satisfy closure
    # for expected commit B.
    decision = ClosurePolicy.evaluate(
        **_ALL_TRUE_KWARGS,
        expected_commit="new-commit",
        ci_result=_ci_result("old-commit", CIStatus.GREEN),
    )

    assert not decision.passed


def test_not_closed_when_ci_failed() -> None:
    decision = ClosurePolicy.evaluate(
        **_ALL_TRUE_KWARGS,
        expected_commit="abc123",
        ci_result=_ci_result("abc123", CIStatus.FAILED),
    )

    assert not decision.passed


def test_ci_green_alone_is_not_sufficient_for_closure() -> None:
    # SPEC Section 46 / INV-18: CI GREEN alone is not CLOSED.
    kwargs = dict(_ALL_TRUE_KWARGS)
    kwargs["ready_to_commit_applicable"] = False
    decision = ClosurePolicy.evaluate(
        **kwargs,
        expected_commit="abc123",
        ci_result=_ci_result("abc123", CIStatus.GREEN),
    )

    assert not decision.passed


def test_repository_mismatch_blocks_closure_even_with_green_ci() -> None:
    kwargs = dict(_ALL_TRUE_KWARGS)
    kwargs["repository_mismatch"] = True
    decision = ClosurePolicy.evaluate(
        **kwargs,
        expected_commit="abc123",
        ci_result=_ci_result("abc123", CIStatus.GREEN),
    )

    assert not decision.passed


def test_pushed_alone_is_not_closed() -> None:
    kwargs = dict(_ALL_TRUE_KWARGS)
    kwargs["human_commit_approval_applicable"] = False
    decision = ClosurePolicy.evaluate(
        **kwargs,
        expected_commit="abc123",
        ci_result=_ci_result("abc123", CIStatus.GREEN),
    )

    assert not decision.passed


def test_closure_is_not_manually_assignable() -> None:
    # There is no setter/flag on ClosurePolicy: the only way to get a
    # passing decision is to satisfy every evaluate() input.
    assert not hasattr(ClosurePolicy, "mark_closed")
    assert not hasattr(ClosurePolicy, "close")
