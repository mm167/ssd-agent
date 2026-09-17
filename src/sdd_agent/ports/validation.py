"""`ValidationRunner` port (TASKS T006 Scope: "ValidationRunner port"; PLAN
Sections 30, 33; SPEC Sections 18-21).

Exposes execution of exactly one already-identified `ValidationObligation`
against one candidate context, producing a structured `ValidationResult`. The
Core "shall not depend on Maven, Gradle, pytest, npm or another particular
validation technology" (PLAN Section 30) -- this port depends on none of
them; `SubprocessValidationRunner` (`sdd_agent.adapters.validation`) is the
concrete, project-agnostic V1 implementation.

*Discovering* which obligations are required for a TASK/project (PLAN
Section 31: discovery and execution are separate responsibilities) is not
this port's concern -- callers (T011/T017/project configuration) supply the
`ValidationObligation` to run. Looping over multiple obligations for one
VALIDATION phase, retry policy, and deciding when validations must be
(re-)run are T011 orchestration concerns, not this port's.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult


class ValidationRunner(ABC):
    """Provider-neutral contract for executing one validation obligation."""

    @abstractmethod
    def run(
        self,
        obligation: ValidationObligation,
        context: EvidenceContext,
        *,
        result_id: str,
    ) -> ValidationResult:
        """Execute `obligation` for the exact candidate identified by `context`.

        `result_id` is caller-supplied (matching this codebase's convention
        for every other durable-evidence identifier -- `report_id`,
        `decision_id`, `waiver_id` are never generated inside a model or
        service) so the caller controls correlation with its own event
        journal (PLAN Section 84).

        Must never raise merely because the obligation's command failed or
        could not be found/completed in time: `ValidationStatus.FAILED` and
        `ValidationStatus.NOT_RUN` (with diagnostics attached via
        `ValidationResult.evidence_reference`) are the expected structured
        outcomes for those cases (SPEC Sections 19-20; PLAN Section 33). An
        implementation may still raise a technical error (e.g.
        `sdd_agent.diagnostics.errors.ValidationExecutionError`) for a
        genuinely unexpected execution-infrastructure failure that is not
        one of those named, classifiable cases.
        """
