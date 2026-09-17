from __future__ import annotations

import pytest

from sdd_agent.configuration.loader import parse_config
from sdd_agent.configuration.secrets import (
    find_secret_like_keys,
    find_secret_like_values,
    reject_secrets,
)
from sdd_agent.diagnostics.errors import ConfigurationError


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "API_KEY",
        "secret",
        "token",
        "github_token",
        "password",
        "credential",
        "access_key",
    ],
)
def test_find_secret_like_keys_detects_common_patterns(key: str) -> None:
    data = {"agents": {}, "ci": {key: "value"}}

    found = find_secret_like_keys(data)

    assert any(key in path for path in found)


def test_find_secret_like_keys_ignores_clean_configuration() -> None:
    data = {"agents": {"readiness": "fake"}, "ci": {"provider": "fake"}}

    assert find_secret_like_keys(data) == []


def test_reject_secrets_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        reject_secrets({"ci": {"provider": "fake", "api_key": "sk-live-123"}})


def test_reject_secrets_allows_clean_configuration() -> None:
    reject_secrets({"agents": {"readiness": "fake"}, "ci": {"provider": "fake"}})


@pytest.mark.parametrize(
    "credential_text",
    [
        "provider returned ghp_SYNTHETICCredentialValue",
        "provider returned github_pat_SYNTHETICCredentialValue",
        "provider returned sk-ant-syntheticCredentialValue",
        "provider returned sk-proj-syntheticCredentialValue",
        "provider returned AKIA1234567890ABCDEF",
        "provider returned AIzaSyntheticCredentialValue",
    ],
)
def test_find_secret_like_values_detects_bare_provider_credentials_in_free_text(
    credential_text: str,
) -> None:
    data = {"payload": {"agent_stdout": credential_text}}

    found = find_secret_like_values(data)

    assert found == ["payload.agent_stdout"]


@pytest.mark.parametrize(
    "safe_text",
    [
        "commit 0123456789abcdef0123456789abcdef01234567",
        "fingerprint e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "session fake-session-2026-09-17",
        "uuid 123e4567-e89b-12d3-a456-426614174000",
        "report readiness-report-2026-09-17-001",
        "ordinary diagnostic text without credentials",
    ],
)
def test_find_secret_like_values_allows_legitimate_identifiers_in_free_text(
    safe_text: str,
) -> None:
    data = {"payload": {"diagnostics": safe_text}}

    assert find_secret_like_values(data) == []


def test_parse_config_rejects_secret_before_schema_validation() -> None:
    yaml_with_secret = """
agents:
  readiness: fake
  implementer: fake
  reviewer: fake
ci:
  provider: fake
  api_key: super-secret-value
"""
    with pytest.raises(ConfigurationError) as excinfo:
        parse_config(yaml_with_secret)

    assert "secret" in str(excinfo.value).lower()


# --- T001-R001 regression: credential-bearing URL values ------------------
#
# Secret-shaped *keys* were already rejected, but a credential embedded in
# the *value* of an otherwise ordinary field (e.g. `git.remote`) previously
# passed through untouched. See PLAN Section 78.

_CREDENTIAL_BEARING_URLS = [
    # The exact value reported by the independent reviewer (T001-R001).
    "https://x-access-token:ghp_exampleSecret@github.com/org/repo.git",
    # Equivalent credential-bearing forms: not GitHub-specific, not
    # HTTPS-specific, and with a userinfo-style secret rather than a token
    # prefix -- proving the rule is structural, not a literal-value match.
    "http://user:hunter2@example.com/repo.git",
    "ssh://git:s3cr3t-pass@example.com/org/repo.git",
    "https://deploy:p%40ssw0rd@gitlab.example.com/group/project.git",
]

_LEGITIMATE_REMOTES = [
    "origin",
    "https://github.com/org/repo.git",
    "https://github.com/org/repo",
    "ssh://git@github.com/org/repo.git",
    "git@github.com:org/repo.git",
    "https://x-access-token@github.com/org/repo.git",  # username only, no password
]


@pytest.mark.parametrize("credential_url", _CREDENTIAL_BEARING_URLS)
def test_find_secret_like_values_detects_credential_bearing_urls(credential_url: str) -> None:
    data = {"git": {"remote": credential_url}}

    found = find_secret_like_values(data)

    assert found == ["git.remote"]


@pytest.mark.parametrize("legitimate_remote", _LEGITIMATE_REMOTES)
def test_find_secret_like_values_allows_legitimate_remotes(legitimate_remote: str) -> None:
    data = {"git": {"remote": legitimate_remote}}

    assert find_secret_like_values(data) == []


def test_reject_secrets_rejects_credential_bearing_url_value() -> None:
    with pytest.raises(ConfigurationError):
        reject_secrets(
            {"git": {"remote": "https://x-access-token:ghp_exampleSecret@github.com/org/repo.git"}}
        )


def test_reject_secrets_allows_legitimate_remote_value() -> None:
    reject_secrets({"git": {"remote": "https://github.com/org/repo.git"}})


def test_parse_config_rejects_credential_bearing_git_remote() -> None:
    """Reproduces the exact T001-R001 finding end-to-end through parse_config."""
    yaml_with_credential_url = """
agents:
  readiness: fake
  implementer: fake
  reviewer: fake

git:
  remote: "https://x-access-token:ghp_exampleSecret@github.com/org/repo.git"
  target_branch: main

ci:
  provider: fake
"""
    with pytest.raises(ConfigurationError) as excinfo:
        parse_config(yaml_with_credential_url)

    assert "secret" in str(excinfo.value).lower()
    assert "git.remote" in excinfo.value.details.get("offending_values", [])


def test_parse_config_accepts_legitimate_git_remote() -> None:
    """Positive regression: the fix must not make git.remote unusable."""
    yaml_with_legitimate_remote = """
agents:
  readiness: fake
  implementer: fake
  reviewer: fake

git:
  remote: "https://github.com/org/repo.git"
  target_branch: main

ci:
  provider: fake
"""
    config = parse_config(yaml_with_legitimate_remote)

    assert config.git.remote == "https://github.com/org/repo.git"
