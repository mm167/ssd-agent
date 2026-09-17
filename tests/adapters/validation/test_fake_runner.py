from __future__ import annotations

import pytest

from sdd_agent.adapters.validation.fake import FakeValidationRunner
from sdd_agent.domain.models.enums import ValidationStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.validation import ValidationObligation


def _obligation(obligation_id: str = "obl-1") -> ValidationObligation:
    return ValidationObligation(
        obligation_id=obligation_id,
        description="d",
        execution_reference="pytest",
        required=True,
    )


def _context() -> EvidenceContext:
    return EvidenceContext(task_id="T006", attempt_id="a1", candidate_id="cand-1")


def test_returns_scripted_passed_status() -> None:
    runner = FakeValidationRunner({"obl-1": ValidationStatus.PASSED})
    result = runner.run(_obligation(), _context(), result_id="r1")

    assert result.status is ValidationStatus.PASSED
    assert result.exit_code == 0
    assert runner.calls == ["obl-1"]


def test_returns_scripted_failed_status() -> None:
    runner = FakeValidationRunner({"obl-1": ValidationStatus.FAILED})
    result = runner.run(_obligation(), _context(), result_id="r1")

    assert result.status is ValidationStatus.FAILED
    assert result.exit_code == 1


def test_not_run_scripted_status_has_no_exit_code() -> None:
    runner = FakeValidationRunner({"obl-1": ValidationStatus.NOT_RUN})
    result = runner.run(_obligation(), _context(), result_id="r1")

    assert result.status is ValidationStatus.NOT_RUN
    assert result.exit_code is None


def test_unscripted_obligation_raises_rather_than_guessing() -> None:
    runner = FakeValidationRunner({})

    with pytest.raises(KeyError):
        runner.run(_obligation("unscripted"), _context(), result_id="r1")
