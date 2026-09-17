"""Concrete and test-double `AgentRunner` implementations.

T007 provides only `FakeAgentRunner`; Claude Code and Codex adapters are
future TASKS T009 and T010.
"""

from sdd_agent.adapters.agents.fake import FakeAgentOutcome, FakeAgentRunner

__all__ = [
    "FakeAgentOutcome",
    "FakeAgentRunner",
]
