"""`AgentRunner` port (TASKS T007; PLAN Sections 13 and 15).

The Core talks to AI coding agents through this provider-neutral abstraction.
Concrete Claude Code and Codex process mechanics are intentionally absent
from the port and belong to T009/T010 adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sdd_agent.domain.models.agent import AgentRequest, AgentResult


class AgentRunner(ABC):
    """Provider-neutral contract for one structured agent execution."""

    @abstractmethod
    def run(self, request: AgentRequest) -> AgentResult:
        """Execute `request` and return structured execution evidence.

        A runner must not translate timeout, provider failure, malformed
        output, or missing output into a successful result. Those cases must
        be represented as non-successful `AgentExecutionStatus` values or as
        technical `AgentExecutionError`s for unexpected infrastructure
        failures.
        """
