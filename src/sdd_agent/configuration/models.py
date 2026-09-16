"""Project configuration models (PLAN Sections 14, 47, 76, 77, 80, 81).

`sdd.yaml` expresses desired project configuration. It is distinct from
`.sdd/` observed operational workflow state, which later TASKS own.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentRole(StrEnum):
    """A workflow responsibility that requires an AI agent (PLAN Section 14).

    AgentRole is intentionally distinct from AgentProvider: which roles exist
    is an architectural/workflow concept, while which provider fills a role
    is pure configuration.
    """

    READINESS = "readiness"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"


class AgentProvider(StrEnum):
    """A concrete AI agent backend an AgentRole may be bound to (PLAN Section 14).

    No AgentRole/AgentProvider pairing (e.g. IMPLEMENTER == Claude Code) is a
    Core invariant; the pairing is expressed entirely through configuration.
    """

    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    FAKE = "fake"


class CIProviderName(StrEnum):
    """A concrete hosted CI backend (PLAN Section 47)."""

    GITHUB_ACTIONS = "github-actions"
    FAKE = "fake"


class AgentsConfig(BaseModel):
    """Maps each AgentRole to an AgentProvider (PLAN Section 14)."""

    model_config = ConfigDict(extra="forbid")

    readiness: AgentProvider
    implementer: AgentProvider
    reviewer: AgentProvider

    def provider_for(self, role: AgentRole) -> AgentProvider:
        return getattr(self, role.value)


class GitConfig(BaseModel):
    """Git remote/target-branch configuration (PLAN Section 76)."""

    model_config = ConfigDict(extra="forbid")

    remote: str = "origin"
    target_branch: str = "main"


class CIConfig(BaseModel):
    """Hosted CI provider selection (PLAN Section 47)."""

    model_config = ConfigDict(extra="forbid")

    provider: CIProviderName


class OperationTimeoutsConfig(BaseModel):
    """Configurable timeouts for external operations (PLAN Section 80).

    A timeout is execution evidence; it is not automatically classified as a
    CODE defect.
    """

    model_config = ConfigDict(extra="forbid")

    claude_code_seconds: float = Field(default=600.0, gt=0)
    codex_seconds: float = Field(default=600.0, gt=0)
    validation_command_seconds: float = Field(default=900.0, gt=0)
    git_network_seconds: float = Field(default=120.0, gt=0)
    ci_polling_seconds: float = Field(default=600.0, gt=0)


class RetryConfig(BaseModel):
    """Bounded retry configuration for eligible technical/transient failures
    (PLAN Section 81).

    Retry is a purely technical concept. This configuration only bounds
    *how* an eligible retry behaves; it is the responsibility of calling
    code (not this model) to keep retries away from workflow-level outcomes
    such as BLOCKER/IMPORTANT findings, validation FAILED, *_REQUIRED
    decisions, or human decisions.
    """

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_backoff_seconds: float = Field(default=1.0, gt=0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    max_backoff_seconds: float = Field(default=60.0, gt=0)

    @field_validator("max_backoff_seconds")
    @classmethod
    def _max_backoff_at_least_initial(cls, value: float, info: Any) -> float:
        initial = info.data.get("initial_backoff_seconds")
        if initial is not None and value < initial:
            raise ValueError("max_backoff_seconds must be >= initial_backoff_seconds")
        return value


class SddConfig(BaseModel):
    """Root project configuration parsed from `sdd.yaml` (PLAN Section 76)."""

    model_config = ConfigDict(extra="forbid")

    agents: AgentsConfig
    git: GitConfig = Field(default_factory=GitConfig)
    ci: CIConfig
    timeouts: OperationTimeoutsConfig = Field(default_factory=OperationTimeoutsConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
