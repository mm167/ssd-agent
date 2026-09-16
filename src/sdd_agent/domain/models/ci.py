"""Provider-neutral CI evidence (SPEC Sections 40-45; PLAN Sections 48-49).

`CIResult` is bound to `expected_commit`, not `candidate_id`: after COMMIT,
workflow identity pivots from candidate fingerprint to an immutable expected
Git commit SHA (PLAN Section 26), and CI evidence must reference that exact
commit (PLAN Section 48, SPEC INV-19). This is why `CIResult` does not embed
`EvidenceContext` (which is candidate-shaped) and instead carries
`expected_commit` directly.

Concrete provider fetching (GitHub Actions polling and run parsing) belongs
to T014/T015; this model is only the target shape their evidence is
translated into.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ConfigDict, Field

from sdd_agent.domain.models.enums import CIStatus
from sdd_agent.domain.models.schema import SchemaVersioned


class CIResult(SchemaVersioned):
    """A normalized, provider-neutral Hosted CI observation for one expected
    commit (SPEC Section 40; PLAN Sections 48-49)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    result_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    expected_commit: str = Field(min_length=1)
    status: CIStatus
    provider_run_reference: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
