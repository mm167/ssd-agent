"""Shared evidence-identity/applicability context (PLAN Section 12).

`EvidenceContext` is the minimal identity durable workflow evidence must
carry so a later deterministic gate policy (owned by T005) can determine
whether that evidence still applies to the exact current workflow context.
T002 defines this shape and a pure identity comparison; it does not implement
gate policies, invalidation rules, or repository-derived identity values
themselves (those belong to T004/T005 and later TASKS).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvidenceContext(BaseModel):
    """The identity a piece of durable evidence is bound to (PLAN Section 12).

    `candidate_id` and `artifact_contract_identity` are optional because some
    evidence (e.g. a ReadinessReport) is produced before a candidate exists,
    or before an artifact-contract identity is meaningful to compare.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    candidate_id: str | None = None
    artifact_contract_identity: str | None = None

    def applies_to(self, other: "EvidenceContext") -> bool:
        """Whether this context still satisfies the identity of `other`.

        Comparison is exact on every field, including `None`: a context whose
        `candidate_id` is not yet established only matches another context
        whose `candidate_id` is equally unestablished. This implements
        nothing beyond SPEC's baseline exact-identity comparison (e.g. SPEC
        Section 17, INV-13, INV-17); callers needing a different applicability
        rule for a specific gate compose their own comparison on top of this.
        """
        return (
            self.task_id == other.task_id
            and self.attempt_id == other.attempt_id
            and self.candidate_id == other.candidate_id
            and self.artifact_contract_identity == other.artifact_contract_identity
        )
