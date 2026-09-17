"""Shared pure gate-decision result shape (PLAN Sections 11, 62).

Every deterministic gate policy in this package returns a `GateDecision`
rather than raising, mutating shared state, or returning a bare boolean: a
refused gate must always be explainable (SPEC Section 62 "Explainable
Command Refusal"). `passed` is the only field a caller may use to authorize
a transition; `reasons` is explanatory context for STATUS/CLI output and
carries no authority of its own.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GateDecision:
    """The outcome of evaluating one deterministic gate."""

    passed: bool
    reasons: tuple[str, ...] = ()
