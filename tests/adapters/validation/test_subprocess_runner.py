from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sdd_agent.adapters.validation.subprocess_runner import SubprocessValidationRunner
from sdd_agent.diagnostics.errors import ValidationExecutionError
from sdd_agent.domain.models.enums import ValidationStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.validation import ValidationObligation


def _obligation(execution_reference: str, obligation_id: str = "obl-1") -> ValidationObligation:
    return ValidationObligation(
        obligation_id=obligation_id,
        description="test obligation",
        execution_reference=execution_reference,
        required=True,
    )


def _context() -> EvidenceContext:
    return EvidenceContext(task_id="T006", attempt_id="a1", candidate_id="cand-1")


def _runner(tmp_path: Path, **kwargs: object) -> SubprocessValidationRunner:
    return SubprocessValidationRunner(cwd=tmp_path, **kwargs)  # type: ignore[arg-type]


# -- PASSED / FAILED / NOT_RUN -------------------------------------------


def test_exit_code_zero_is_passed(tmp_path: Path) -> None:
    obligation = _obligation(f'{sys.executable} -c "raise SystemExit(0)"')
    result = _runner(tmp_path).run(obligation, _context(), result_id="r1")

    assert result.status is ValidationStatus.PASSED
    assert result.exit_code == 0
    assert result.result_id == "r1"
    assert result.obligation_id == "obl-1"
    assert result.context == _context()


def test_nonzero_exit_code_is_failed(tmp_path: Path) -> None:
    obligation = _obligation(f'{sys.executable} -c "raise SystemExit(1)"')
    result = _runner(tmp_path).run(obligation, _context(), result_id="r1")

    assert result.status is ValidationStatus.FAILED
    assert result.exit_code == 1


def test_missing_executable_is_not_run(tmp_path: Path) -> None:
    obligation = _obligation("definitely-not-a-real-executable-xyz")
    result = _runner(tmp_path).run(obligation, _context(), result_id="r1")

    assert result.status is ValidationStatus.NOT_RUN
    assert result.exit_code is None
    assert result.evidence_reference is None  # no evidence_dir configured


def test_timeout_is_not_run(tmp_path: Path) -> None:
    obligation = _obligation(f'{sys.executable} -c "import time; time.sleep(5)"')
    result = _runner(tmp_path, timeout_seconds=0.2).run(obligation, _context(), result_id="r1")

    assert result.status is ValidationStatus.NOT_RUN
    assert result.exit_code is None


# -- adversarial: never launder a real failure into PASSED ----------------


def test_never_reports_passed_without_actual_zero_exit(tmp_path: Path) -> None:
    obligation = _obligation(f'{sys.executable} -c "print(\'PASSED\'); raise SystemExit(3)"')
    result = _runner(tmp_path).run(obligation, _context(), result_id="r1")

    assert result.status is ValidationStatus.FAILED
    assert result.exit_code == 3


def test_result_never_embeds_raw_stdout(tmp_path: Path) -> None:
    obligation = _obligation(f'{sys.executable} -c "print(\'x\' * 10000)"')
    result = _runner(tmp_path).run(obligation, _context(), result_id="r1")

    # ValidationResult (T002) has no stdout/stderr field at all: large
    # command logs are never embedded in the primary workflow-state model
    # (PLAN Section 37).
    assert not hasattr(result, "stdout")
    assert not hasattr(result, "stderr")


# -- evidence storage -------------------------------------------------


def test_evidence_written_when_evidence_dir_configured(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    obligation = _obligation(f'{sys.executable} -c "print(\'hello\')"')
    result = _runner(tmp_path, evidence_dir=evidence_dir).run(obligation, _context(), result_id="r1")

    assert result.evidence_reference is not None
    evidence_path = Path(result.evidence_reference)
    assert evidence_path.is_file()
    assert evidence_path.parent == evidence_dir
    assert "hello" in evidence_path.read_text(encoding="utf-8")


def test_evidence_with_credential_bearing_execution_reference_is_refused(tmp_path: Path) -> None:
    # Cross-finding regression probe 7: evidence_dir configured.
    evidence_dir = tmp_path / "evidence"
    obligation = _obligation("https://user:secretpassword@example.com/run-validate")

    with pytest.raises(ValidationExecutionError):
        _runner(tmp_path, evidence_dir=evidence_dir).run(obligation, _context(), result_id="r1")

    assert not (evidence_dir / "r1.json").exists()
    assert not evidence_dir.exists() or not any(evidence_dir.iterdir())


def test_credential_bearing_execution_reference_refused_without_evidence_dir(tmp_path: Path) -> None:
    # T006-IR-003 / cross-finding regression probe 6: no evidence_dir at all
    # -- the secret must still never reach the *returned* ValidationResult.
    obligation = _obligation("https://user:secretpassword@example.com/run-validate")

    with pytest.raises(ValidationExecutionError) as excinfo:
        _runner(tmp_path).run(obligation, _context(), result_id="r1")

    # The secret value itself must never appear in the raised message.
    assert "secretpassword" not in str(excinfo.value)
