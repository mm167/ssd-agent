from __future__ import annotations

import pytest

from sdd_agent.configuration.loader import load_config, parse_config
from sdd_agent.configuration.models import AgentProvider, CIProviderName, SddConfig
from sdd_agent.diagnostics.errors import ConfigurationError

VALID_YAML = """
agents:
  readiness: codex
  implementer: claude-code
  reviewer: codex

git:
  remote: origin
  target_branch: main

ci:
  provider: github-actions
"""


def test_valid_configuration_parses() -> None:
    config = parse_config(VALID_YAML)

    assert isinstance(config, SddConfig)
    assert config.agents.readiness is AgentProvider.CODEX
    assert config.agents.implementer is AgentProvider.CLAUDE_CODE
    assert config.agents.reviewer is AgentProvider.CODEX
    assert config.git.remote == "origin"
    assert config.git.target_branch == "main"
    assert config.ci.provider is CIProviderName.GITHUB_ACTIONS


def test_valid_configuration_applies_defaults() -> None:
    minimal_yaml = """
agents:
  readiness: fake
  implementer: fake
  reviewer: fake
ci:
  provider: fake
"""
    config = parse_config(minimal_yaml)

    assert config.git.remote == "origin"
    assert config.git.target_branch == "main"
    assert config.timeouts.claude_code_seconds > 0
    assert config.retry.max_attempts >= 1


def test_load_config_reads_from_file(tmp_path) -> None:
    config_path = tmp_path / "sdd.yaml"
    config_path.write_text(VALID_YAML, encoding="utf-8")

    config = load_config(config_path)

    assert config.agents.implementer is AgentProvider.CLAUDE_CODE


def test_load_config_missing_file_is_rejected(tmp_path) -> None:
    with pytest.raises(ConfigurationError):
        load_config(tmp_path / "does-not-exist.yaml")


@pytest.mark.parametrize(
    "invalid_yaml",
    [
        # Unknown provider name.
        "agents:\n  readiness: not-a-real-provider\n  implementer: fake\n  reviewer: fake\nci:\n  provider: fake\n",
        # Missing required role.
        "agents:\n  readiness: fake\n  implementer: fake\nci:\n  provider: fake\n",
        # Missing required top-level section.
        "agents:\n  readiness: fake\n  implementer: fake\n  reviewer: fake\n",
        # Not a mapping at all.
        "not-a-mapping",
        # Unknown field rejected (strict schema).
        "agents:\n  readiness: fake\n  implementer: fake\n  reviewer: fake\nci:\n  provider: fake\n  extra_unknown_field: true\n",
    ],
)
def test_invalid_configuration_is_rejected(invalid_yaml: str) -> None:
    with pytest.raises(ConfigurationError):
        parse_config(invalid_yaml)


def test_invalid_yaml_syntax_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        parse_config("agents: [unclosed")


def test_configuration_error_is_explainable() -> None:
    with pytest.raises(ConfigurationError) as excinfo:
        parse_config("agents:\n  readiness: fake\n  implementer: fake\n  reviewer: fake\n")

    assert "ci" in str(excinfo.value).lower() or excinfo.value.details
