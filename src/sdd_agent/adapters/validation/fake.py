"""Deterministic `ValidationRunner` test double (TASKS T006; PLAN Section 97).

`FakeValidationRunner` lets later TASKS (T011, T018) test orchestration and
scenario behavior without invoking real subprocesses. It is mandatory for
deterministic tests and does not replace `SubprocessValidationRunner`
(PLAN Section 97: fake adapters "do not replace the required concrete V1
adapters").
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from sdd_agent.domain.models.enums import ValidationStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult
from sdd_agent.ports.validation import ValidationRunner

_DEFAULT_EXIT_CODE_BY_STATUS: dict[ValidationStatus, int | None] = {
    ValidationStatus.PASSED: 0,
    ValidationStatus.FAILED: 1,
    ValidationStatus.NOT_RUN: None,
}


class FakeValidationRunner(ValidationRunner):
    """Scripted `ValidationRunner`: one outcome per `obligation_id`.

    Running an obligation with no scripted outcome raises rather than
    silently returning a default status, so a test fixture must be explicit
    about every obligation it expects to be executed (matching this
    codebase's existing `FakeAgentRunner`-style convention of failing loudly
    on an unscripted call rather than guessing).
    """

    def __init__(self, scripted_statuses: Mapping[str, ValidationStatus]) -> None:
        self._scripted = dict(scripted_statuses)
        self.calls: list[str] = []

    def run(
        self,
        obligation: ValidationObligation,
        context: EvidenceContext,
        *,
        result_id: str,
    ) -> ValidationResult:
        self.calls.append(obligation.obligation_id)
        if obligation.obligation_id not in self._scripted:
            raise KeyError(
                f"FakeValidationRunner has no scripted status for obligation "
                f"{obligation.obligation_id!r}"
            )
        status = self._scripted[obligation.obligation_id]
        now = datetime.now(timezone.utc)
        return ValidationResult(
            result_id=result_id,
            obligation_id=obligation.obligation_id,
            context=context,
            status=status,
            execution_reference=obligation.execution_reference,
            exit_code=_DEFAULT_EXIT_CODE_BY_STATUS[status],
            started_at=now,
            completed_at=now,
        )
