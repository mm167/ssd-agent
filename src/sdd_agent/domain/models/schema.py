"""Shared schema-version convention for persistable domain models (TASKS T002
Deliverables: "Shared schema/version conventions"; PLAN Sections 62-64, 69).

T002 owns only this convention. Reading/writing these models under `.sdd/`,
schema-version compatibility enforcement, and corrupt-state detection belong
to T003.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

CURRENT_SCHEMA_VERSION = 1


class SchemaVersioned(BaseModel):
    """Base for any domain model that may later be persisted under `.sdd/`.

    Carrying an explicit `schema_version` on the model itself (rather than
    only on its eventual storage envelope) lets a future SDD Agent version
    detect and reject data written by an incompatible older schema before it
    ever reaches domain logic (PLAN Section 69 concept).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=CURRENT_SCHEMA_VERSION, ge=1)
