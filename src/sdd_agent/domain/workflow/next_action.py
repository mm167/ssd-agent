"""`NextAuthorizedActionPolicy` (PLAN Section 9.3; TASKS T005; T002
`NextAuthorizedAction`).

T002's `NextAuthorizedAction.action` docstring explicitly assigns ownership of
"the closed set of valid actions" to T005 ("a gate concern owned by T005, not
a value this model constrains"). This module is that closed set and the
deterministic policy that derives it.

PLAN Section 9.3 gives exactly one concrete action literal --
`RESOLVE_ENVIRONMENT`, for an `ENVIRONMENT_BLOCKED` condition -- and by doing
so establishes a `RESOLVE_<subject>` naming convention for a Condition that
requires an external (human/artifact/dependency) resolution before
progression. PLAN Section 61's STATUS example gives one more literal: `FIX`,
for a `FIX_REQUIRED` condition. `FIX_REQUIRED` deliberately breaks the
`RESOLVE_` pattern in that same example: unlike the other conditions, it does
not describe something requiring *external* resolution -- it describes an
internal SDD Phase (`Phase.FIX`) the workflow is already authorized to enter.
This module reuses that same "the action is the Phase you may now enter"
idea for every unblocked case: when no Condition blocks progression, the
action is the `Phase.value` (upper-cased to match PLAN's own display
convention, e.g. "FIX", "IMPLEMENTATION") of an explicitly supplied
`target_phase`, which is validated for structural legality through
`sdd_agent.domain.workflow.transitions.authorize_transition` before ever
being represented as an authorized action -- an illegal proposed target
raises rather than being silently corrected, ignored, or defaulted.

This module does not decide *which* of several structurally valid forward
phases is contextually correct (e.g. REVIEW vs RE_REVIEW after VALIDATION,
or FIX vs READY_TO_COMMIT after REVIEW): SPEC/PLAN define no durable fact
this policy could use to make that call on its own, and T002's `Attempt`
model carries no such field (e.g. no review-cycle counter). That choice is
an orchestration-level decision (T011), which must already know it and
supplies it as `target_phase`; this policy only ever validates and
represents that choice, never makes or performs it.

A `Condition` is never authoritative on its own: it only ever means anything
*within* the specific `Phase` where SPEC/PLAN describe it arising. A
`Condition` presented against a `Phase` it cannot arise in (e.g.
`FIX_REQUIRED` -- "a blocking CODE finding requires FIX" -- claimed while
`current_phase` is `READINESS`, where no CODE exists yet to have a finding
about) is an incoherent pair and is rejected before any action is derived,
exactly like an unauthorized `Phase` transition is rejected by
`transitions.authorize_transition`.
"""

from __future__ import annotations

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.domain.models.attempt import NextAuthorizedAction
from sdd_agent.domain.models.enums import Condition, Phase
from sdd_agent.domain.workflow.transitions import (
    ARTIFACT_RETURN_ELIGIBLE_PHASES,
    TERMINAL_PHASES,
    authorize_transition,
)

_RESOLUTION_ACTION: dict[Condition, str] = {
    Condition.SPEC_REQUIRED: "RESOLVE_SPEC",
    Condition.PLAN_REQUIRED: "RESOLVE_PLAN",
    Condition.TASKS_REQUIRED: "RESOLVE_TASKS",
    Condition.ENVIRONMENT_BLOCKED: "RESOLVE_ENVIRONMENT",
    Condition.REPOSITORY_MISMATCH: "RESOLVE_REPOSITORY_MISMATCH",
    Condition.TASK_DEPENDENCY_UNSATISFIED: "RESOLVE_DEPENDENCY",
    Condition.FIX_REQUIRED: "FIX",
}
"""The closed `NextAuthorizedAction.action` vocabulary for a blocking
Condition (PLAN Sections 9.3, 61). Exhaustive over every `Condition` member:
a dict lookup for a member missing from this map raises `KeyError` rather
than silently falling through to a default action.
"""

_ARTIFACT_AMBIGUITY_PHASES: frozenset[Phase] = frozenset({Phase.READINESS}) | ARTIFACT_RETURN_ELIGIBLE_PHASES
"""Phases in which `SPEC_REQUIRED`/`PLAN_REQUIRED`/`TASKS_REQUIRED` are
coherent: READINESS itself (SPEC Section 14, where artifact ambiguity is
first discovered) plus every phase from which an approved artifact change
returns the workflow through READINESS (SPEC Sections 16, 20, 29, 35.6,
41-44; `transitions.ARTIFACT_RETURN_ELIGIBLE_PHASES`).
"""

_CODE_OR_ENVIRONMENT_FINDING_PHASES: frozenset[Phase] = ARTIFACT_RETURN_ELIGIBLE_PHASES - {Phase.IMPLEMENTATION}
"""Phases in which `FIX_REQUIRED`/`ENVIRONMENT_BLOCKED` are coherent:
VALIDATION (SPEC Section 20 validation-failure classification), REVIEW/
RE_REVIEW (SPEC Section 29 finding routing includes both CODE and
ENVIRONMENT), READY_TO_COMMIT (SPEC Section 35.6 human-requested-change
routing includes both), and CI (SPEC Sections 41-44 CI-failure
classification includes both). IMPLEMENTATION is excluded: SPEC Section 16
"Artifact Return During Implementation" only ever routes IMPLEMENTATION to
SPEC_REQUIRED/PLAN_REQUIRED/TASKS_REQUIRED -- there is no CODE finding to fix
(IMPLEMENTATION *is* where CODE work already happens) and no validation
command has run yet to fail with an ENVIRONMENT cause.
"""

_CONDITION_VALID_PHASES: dict[Condition, frozenset[Phase]] = {
    Condition.SPEC_REQUIRED: _ARTIFACT_AMBIGUITY_PHASES,
    Condition.PLAN_REQUIRED: _ARTIFACT_AMBIGUITY_PHASES,
    Condition.TASKS_REQUIRED: _ARTIFACT_AMBIGUITY_PHASES,
    Condition.TASK_DEPENDENCY_UNSATISFIED: frozenset({Phase.READINESS}),
    Condition.FIX_REQUIRED: _CODE_OR_ENVIRONMENT_FINDING_PHASES,
    Condition.ENVIRONMENT_BLOCKED: _CODE_OR_ENVIRONMENT_FINDING_PHASES,
    Condition.REPOSITORY_MISMATCH: frozenset(Phase) - TERMINAL_PHASES,
}
"""The Phase x Condition compatibility matrix (SPEC Sections 9-10, 14, 16,
20, 29, 35.6, 41-48, 50; PLAN Sections 29, 46, 90). Exhaustive over every
`Condition` member.

`TASK_DEPENDENCY_UNSATISFIED` is valid only in READINESS (SPEC Section 9:
dependency evaluation is a READINESS-time concern). `REPOSITORY_MISMATCH` is
valid in every non-terminal phase (SPEC Sections 48, 50: repository mismatch
is an "external changes during active execution" concern spanning baseline,
candidate, validations, review, READY_TO_COMMIT, approval, expected commit,
remote target, and CI -- i.e. essentially the whole active lifecycle, not one
phase).
"""


class NextAuthorizedActionPolicy:
    """Deterministic `NextAuthorizedAction` derivation (PLAN Section 9.3)."""

    @staticmethod
    def derive(
        *,
        current_phase: Phase,
        blocking_condition: Condition | None,
        target_phase: Phase | None = None,
    ) -> NextAuthorizedAction:
        """Derive the one authorized next action for `current_phase`.

        A `blocking_condition` always wins and `target_phase` must not be
        supplied alongside one: a blocking condition can never be bypassed
        by proposing a phase to move to instead (PLAN Section 58 "No
        Generic Gate Bypass"). Supplying both is treated as an invalid,
        contradictory combination and raises rather than silently
        preferring one input over the other.

        A `blocking_condition` is only ever coherent for specific phases
        (`_CONDITION_VALID_PHASES`); an incoherent `current_phase`/
        `blocking_condition` pair (e.g. READINESS + FIX_REQUIRED) raises
        rather than deriving an action from it -- a Condition is never
        authoritative independently of whether it is valid for the current
        Phase.

        Without a blocking condition, `target_phase` is mandatory and is
        validated for structural legality via `authorize_transition` before
        being represented as the action; an illegal proposed target raises.
        """
        if blocking_condition is not None:
            if target_phase is not None:
                raise WorkflowViolation(
                    "target_phase must not be supplied when a blocking condition is present",
                    details={
                        "current_phase": current_phase.value,
                        "blocking_condition": blocking_condition.value,
                        "target_phase": target_phase.value,
                    },
                )
            if current_phase not in _CONDITION_VALID_PHASES[blocking_condition]:
                raise WorkflowViolation(
                    f"condition {blocking_condition.value} is not valid for phase {current_phase.value}",
                    details={
                        "current_phase": current_phase.value,
                        "blocking_condition": blocking_condition.value,
                    },
                )
            return NextAuthorizedAction(
                action=_RESOLUTION_ACTION[blocking_condition],
                reason=f"blocked: {blocking_condition.value}",
            )

        if target_phase is None:
            raise WorkflowViolation(
                "target_phase is required to derive the next authorized action "
                "when no blocking condition is present",
                details={"current_phase": current_phase.value},
            )

        authorize_transition(current_phase, target_phase)
        return NextAuthorizedAction(action=target_phase.value.upper())
