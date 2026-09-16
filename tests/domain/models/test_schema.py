from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import CURRENT_SCHEMA_VERSION, SchemaVersioned


def test_schema_version_defaults_to_current() -> None:
    model = SchemaVersioned()

    assert model.schema_version == CURRENT_SCHEMA_VERSION


def test_schema_version_can_be_set_explicitly() -> None:
    model = SchemaVersioned(schema_version=1)

    assert model.schema_version == 1


def test_schema_version_rejects_non_positive() -> None:
    with pytest.raises(ValidationError):
        SchemaVersioned(schema_version=0)


def test_schema_versioned_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SchemaVersioned(unexpected="value")
