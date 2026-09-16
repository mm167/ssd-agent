from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import CIResult, CIStatus


def test_ci_result_minimal() -> None:
    result = CIResult(
        result_id="ci1",
        task_id="T002",
        attempt_id="a1",
        expected_commit="a" * 40,
        status=CIStatus.GREEN,
    )

    assert result.status is CIStatus.GREEN


@pytest.mark.parametrize(
    "status",
    [
        CIStatus.PENDING,
        CIStatus.RUNNING,
        CIStatus.GREEN,
        CIStatus.FAILED,
        CIStatus.CANCELLED,
        CIStatus.NOT_FOUND,
    ],
)
def test_ci_result_accepts_each_status(status: CIStatus) -> None:
    result = CIResult(
        result_id="ci1",
        task_id="T002",
        attempt_id="a1",
        expected_commit="a" * 40,
        status=status,
    )

    assert result.status is status


def test_ci_result_rejects_unsupported_status() -> None:
    with pytest.raises(ValidationError):
        CIResult(
            result_id="ci1",
            task_id="T002",
            attempt_id="a1",
            expected_commit="a" * 40,
            status="SUCCESS",
        )


def test_ci_result_requires_expected_commit() -> None:
    with pytest.raises(ValidationError):
        CIResult(
            result_id="ci1",
            task_id="T002",
            attempt_id="a1",
            expected_commit="",
            status=CIStatus.GREEN,
        )


def test_ci_result_has_no_candidate_field() -> None:
    result = CIResult(
        result_id="ci1",
        task_id="T002",
        attempt_id="a1",
        expected_commit="a" * 40,
        status=CIStatus.GREEN,
    )

    assert not hasattr(result, "candidate_id")


def test_ci_result_is_frozen() -> None:
    result = CIResult(
        result_id="ci1",
        task_id="T002",
        attempt_id="a1",
        expected_commit="a" * 40,
        status=CIStatus.GREEN,
    )

    with pytest.raises(ValidationError):
        result.status = CIStatus.FAILED  # type: ignore[misc]
