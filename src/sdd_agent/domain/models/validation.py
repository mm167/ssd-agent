"""Validation obligation, result, and waiver contracts (SPEC Sections 18-22;
PLAN Sections 31-36).

T002 owns only these data shapes and their own internal invariants (e.g. a
waiver's cause must be the single V1-eligible classification). Discovering
and executing obligations belongs to T006's `ValidationRunner`; deciding
whether a given NOT_RUN result plus waiver currently satisfies a gate belongs
to T005/T006.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ConfigDict, Field, model_validator

from sdd_agent.domain.models.enums import ValidationStatus, WaiverEligibleCause
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.schema import SchemaVersioned


class ValidationObligation(SchemaVersioned):
    """An identifiable required (or optional) validation (PLAN Section 32)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    obligation_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    execution_reference: str = Field(min_length=1)
    required: bool
    non_waivable: bool = False


class ValidationResult(SchemaVersioned):
    """Structured outcome of one validation execution (PLAN Section 33).

    `context.candidate_id` is required: a validation result is always bound
    to the exact candidate it was executed against (SPEC Section 21, INV-13).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    result_id: str = Field(min_length=1)
    obligation_id: str = Field(min_length=1)
    context: EvidenceContext
    status: ValidationStatus
    execution_reference: str | None = None
    exit_code: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    evidence_reference: str | None = None

    @model_validator(mode="after")
    def _candidate_required(self) -> "ValidationResult":
        if self.context.candidate_id is None:
            raise ValueError("ValidationResult.context.candidate_id is required")
        return self


class ValidationWaiver(SchemaVersioned):
    """A human-approved exceptional derogation for one NOT_RUN,
    ENVIRONMENT-caused validation obligation (SPEC Section 22; PLAN Sections
    35-36).

    A waiver never turns NOT_RUN into PASSED (SPEC Section 22.3); it is
    evidence a gate policy (T005/T006) may separately choose to accept
    alongside an unresolved NOT_RUN result. Re-evaluating whether a
    previously granted waiver still applies to the current attempt/candidate/
    contract/evidence/cause belongs to T005/T006, not this model.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    waiver_id: str = Field(min_length=1)
    obligation_id: str = Field(min_length=1)
    context: EvidenceContext
    cause: WaiverEligibleCause
    validation_result_id: str = Field(min_length=1)
    human_decision_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _candidate_required(self) -> "ValidationWaiver":
        if self.context.candidate_id is None:
            raise ValueError("ValidationWaiver.context.candidate_id is required")
        return self
