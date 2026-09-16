"""`sdd.yaml` loading and validation (PLAN Sections 76, 77).

Invalid configuration must prevent sensitive operations and produce an
explainable configuration error (PLAN Section 77); it must never silently
proceed with defaults or partial data.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from sdd_agent.configuration.models import SddConfig
from sdd_agent.configuration.secrets import reject_secrets
from sdd_agent.diagnostics.errors import ConfigurationError


def parse_config(raw_yaml: str, *, source: str = "<config>") -> SddConfig:
    """Parse and validate `sdd.yaml` content already read into memory."""
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Configuration at {source} is not valid YAML: {exc}",
            details={"source": source},
        ) from exc

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Configuration at {source} must be a YAML mapping at the top level.",
            details={"source": source},
        )

    reject_secrets(data)

    try:
        return SddConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(
            f"Configuration at {source} is invalid: {exc}",
            details={"source": source, "errors": exc.errors()},
        ) from exc


def load_config(path: Path) -> SddConfig:
    """Load and validate project configuration from an `sdd.yaml` file path."""
    path = Path(path)
    if not path.is_file():
        raise ConfigurationError(
            f"Configuration file not found: {path}",
            details={"path": str(path)},
        )
    raw_yaml = path.read_text(encoding="utf-8")
    return parse_config(raw_yaml, source=str(path))
