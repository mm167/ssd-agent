from __future__ import annotations

import inspect

import pytest

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.domain.models.enums import Condition, Phase
from sdd_agent.domain.workflow.next_action import _CONDITION_VALID_PHASES, NextAuthorizedActionPolicy


@pytest.mark.parametrize(
    ("phase", "condition", "expected_action"),
    [
        # READINESS: SPEC Section 14 (artifact ambiguity) + Section 9
        # (dependency problems). No CODE/ENVIRONMENT finding exists yet.
        (Phase.READINESS, Condition.SPEC_REQUIRED, "RESOLVE_SPEC"),
        (Phase.READINESS, Condition.PLAN_REQUIRED, "RESOLVE_PLAN"),
        (Phase.READINESS, Condition.TASKS_REQUIRED, "RESOLVE_TASKS"),
        (Phase.READINESS, Condition.TASK_DEPENDENCY_UNSATISFIED, "RESOLVE_DEPENDENCY"),
        (Phase.READINESS, Condition.REPOSITORY_MISMATCH, "RESOLVE_REPOSITORY_MISMATCH"),
        # IMPLEMENTATION: SPEC Section 16 -- artifact ambiguity only, no
        # CODE/ENVIRONMENT routing (there is no finding/validation yet).
        (Phase.IMPLEMENTATION, Condition.SPEC_REQUIRED, "RESOLVE_SPEC"),
        (Phase.IMPLEMENTATION, Condition.PLAN_REQUIRED, "RESOLVE_PLAN"),
        (Phase.IMPLEMENTATION, Condition.TASKS_REQUIRED, "RESOLVE_TASKS"),
        (Phase.IMPLEMENTATION, Condition.REPOSITORY_MISMATCH, "RESOLVE_REPOSITORY_MISMATCH"),
        # VALIDATION: SPEC Section 20 -- CODE and ENVIRONMENT both route here.
        (Phase.VALIDATION, Condition.SPEC_REQUIRED, "RESOLVE_SPEC"),
        (Phase.VALIDATION, Condition.PLAN_REQUIRED, "RESOLVE_PLAN"),
        (Phase.VALIDATION, Condition.TASKS_REQUIRED, "RESOLVE_TASKS"),
        (Phase.VALIDATION, Condition.FIX_REQUIRED, "FIX"),
        (Phase.VALIDATION, Condition.ENVIRONMENT_BLOCKED, "RESOLVE_ENVIRONMENT"),
        (Phase.VALIDATION, Condition.REPOSITORY_MISMATCH, "RESOLVE_REPOSITORY_MISMATCH"),
        # REVIEW / RE_REVIEW: SPEC Section 29 finding routing includes CODE
        # and ENVIRONMENT.
        (Phase.REVIEW, Condition.FIX_REQUIRED, "FIX"),
        (Phase.REVIEW, Condition.ENVIRONMENT_BLOCKED, "RESOLVE_ENVIRONMENT"),
        (Phase.REVIEW, Condition.SPEC_REQUIRED, "RESOLVE_SPEC"),
        (Phase.RE_REVIEW, Condition.FIX_REQUIRED, "FIX"),
        (Phase.RE_REVIEW, Condition.ENVIRONMENT_BLOCKED, "RESOLVE_ENVIRONMENT"),
        # READY_TO_COMMIT: SPEC Section 35.6 human-requested-change routing.
        (Phase.READY_TO_COMMIT, Condition.FIX_REQUIRED, "FIX"),
        (Phase.READY_TO_COMMIT, Condition.ENVIRONMENT_BLOCKED, "RESOLVE_ENVIRONMENT"),
        (Phase.READY_TO_COMMIT, Condition.TASKS_REQUIRED, "RESOLVE_TASKS"),
        # CI: SPEC Sections 41-44 CI-failure classification.
        (Phase.CI, Condition.FIX_REQUIRED, "FIX"),
        (Phase.CI, Condition.ENVIRONMENT_BLOCKED, "RESOLVE_ENVIRONMENT"),
        (Phase.CI, Condition.REPOSITORY_MISMATCH, "RESOLVE_REPOSITORY_MISMATCH"),
        # COMMIT / PUSH: only cross-cutting REPOSITORY_MISMATCH (SPEC 39, 48, 50).
        (Phase.COMMIT, Condition.REPOSITORY_MISMATCH, "RESOLVE_REPOSITORY_MISMATCH"),
        (Phase.PUSH, Condition.REPOSITORY_MISMATCH, "RESOLVE_REPOSITORY_MISMATCH"),
    ],
)
def test_valid_phase_condition_pairs_produce_the_authoritative_action(
    phase: Phase, condition: Condition, expected_action: str
) -> None:
    action = NextAuthorizedActionPolicy.derive(current_phase=phase, blocking_condition=condition)

    assert action.action == expected_action


def test_readiness_and_fix_required_is_rejected() -> None:
    # T005-IR-003 (2nd round): the reviewer-demonstrated defect. READINESS
    # has no CODE yet to have a finding about, so FIX_REQUIRED is incoherent
    # against Phase.READINESS and must not authorize FIX.
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(current_phase=Phase.READINESS, blocking_condition=Condition.FIX_REQUIRED)


def test_readiness_and_environment_blocked_is_rejected() -> None:
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(
            current_phase=Phase.READINESS, blocking_condition=Condition.ENVIRONMENT_BLOCKED
        )


def test_implementation_and_fix_required_is_rejected() -> None:
    # SPEC Section 16 "Artifact Return During Implementation" routes only to
    # SPEC_REQUIRED/PLAN_REQUIRED/TASKS_REQUIRED -- there is no CODE finding
    # to fix while still inside IMPLEMENTATION itself.
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(
            current_phase=Phase.IMPLEMENTATION, blocking_condition=Condition.FIX_REQUIRED
        )


def test_validation_and_task_dependency_unsatisfied_is_rejected() -> None:
    # SPEC Section 9: dependency evaluation is a READINESS-time concern only.
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(
            current_phase=Phase.VALIDATION, blocking_condition=Condition.TASK_DEPENDENCY_UNSATISFIED
        )


def test_commit_and_fix_required_is_rejected() -> None:
    # COMMIT/PUSH are short orchestrated Git actions (T013) with no described
    # artifact/CODE/ENVIRONMENT ambiguity-discovery point.
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(current_phase=Phase.COMMIT, blocking_condition=Condition.FIX_REQUIRED)


def test_no_invalid_combination_can_produce_an_allowed_action() -> None:
    for condition, valid_phases in _CONDITION_VALID_PHASES.items():
        for phase in Phase:
            if phase in valid_phases:
                continue
            with pytest.raises(WorkflowViolation):
                NextAuthorizedActionPolicy.derive(current_phase=phase, blocking_condition=condition)


def test_environment_blocked_matches_the_literal_plan_section_9_3_example() -> None:
    action = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.VALIDATION,
        blocking_condition=Condition.ENVIRONMENT_BLOCKED,
    )

    assert action.action == "RESOLVE_ENVIRONMENT"


def test_fix_required_matches_the_literal_plan_section_61_status_example() -> None:
    action = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.REVIEW,
        blocking_condition=Condition.FIX_REQUIRED,
    )

    assert action.action == "FIX"


def test_resolution_action_map_is_exhaustive_over_condition() -> None:
    # T005-IR-003 (2nd round): the original version of this test used
    # Phase.READINESS unconditionally for every Condition, which incorrectly
    # encoded "every Condition is valid from READINESS" -- exactly the
    # reviewer-demonstrated defect (e.g. READINESS + FIX_REQUIRED). Corrected
    # to pick one phase the compatibility matrix itself declares valid for
    # each condition, so it can never mask a coherence violation.
    for condition in Condition:
        valid_phases = _CONDITION_VALID_PHASES[condition]
        assert valid_phases, f"{condition} has no valid phase in the compatibility matrix"
        phase = next(iter(valid_phases))

        action = NextAuthorizedActionPolicy.derive(current_phase=phase, blocking_condition=condition)

        assert isinstance(action.action, str) and action.action


def test_identical_input_produces_identical_action() -> None:
    first = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.VALIDATION, blocking_condition=Condition.ENVIRONMENT_BLOCKED
    )
    second = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.VALIDATION, blocking_condition=Condition.ENVIRONMENT_BLOCKED
    )

    assert first == second


def test_identical_target_phase_input_produces_identical_action() -> None:
    first = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.READINESS, blocking_condition=None, target_phase=Phase.IMPLEMENTATION
    )
    second = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.READINESS, blocking_condition=None, target_phase=Phase.IMPLEMENTATION
    )

    assert first == second


def test_unblocked_action_is_the_authorized_target_phase_name() -> None:
    action = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.READINESS, blocking_condition=None, target_phase=Phase.IMPLEMENTATION
    )

    assert action.action == "IMPLEMENTATION"


def test_both_validation_forward_targets_are_representable() -> None:
    # VALIDATION may reach either REVIEW (first pass) or RE_REVIEW (after
    # FIX); this policy authorizes/represents whichever is proposed rather
    # than picking one itself.
    review_action = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.VALIDATION, blocking_condition=None, target_phase=Phase.REVIEW
    )
    re_review_action = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.VALIDATION, blocking_condition=None, target_phase=Phase.RE_REVIEW
    )

    assert review_action.action == "REVIEW"
    assert re_review_action.action == "RE_REVIEW"


def test_missing_target_phase_without_blocking_condition_is_rejected() -> None:
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(current_phase=Phase.READINESS, blocking_condition=None)


def test_illegal_target_phase_is_rejected() -> None:
    # READINESS may never jump directly to COMMIT (SPEC Section 66).
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(
            current_phase=Phase.READINESS, blocking_condition=None, target_phase=Phase.COMMIT
        )


def test_contradictory_condition_and_target_phase_is_rejected() -> None:
    # A blocking condition can never be bypassed by proposing a phase to
    # move to instead: supplying both is a contradictory combination.
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(
            current_phase=Phase.VALIDATION,
            blocking_condition=Condition.ENVIRONMENT_BLOCKED,
            target_phase=Phase.REVIEW,
        )


def test_no_blocking_condition_can_be_bypassed_by_a_proposed_target_phase() -> None:
    # Re-affirms the contradictory-combination rejection specifically as a
    # bypass-prevention property: even a *legal* target_phase must not be
    # accepted alongside an active blocking condition.
    with pytest.raises(WorkflowViolation):
        NextAuthorizedActionPolicy.derive(
            current_phase=Phase.REVIEW,
            blocking_condition=Condition.FIX_REQUIRED,
            target_phase=Phase.FIX,
        )


def test_no_force_or_skip_bypass_parameter_exists() -> None:
    signature = inspect.signature(NextAuthorizedActionPolicy.derive)
    assert set(signature.parameters) == {"current_phase", "blocking_condition", "target_phase"}


def test_no_provider_parameter_influences_the_decision() -> None:
    signature = inspect.signature(NextAuthorizedActionPolicy.derive)
    assert "provider" not in signature.parameters
    assert "agent" not in signature.parameters


def test_derive_returns_a_value_and_performs_no_action() -> None:
    # Authorization is pure representation: the returned NextAuthorizedAction
    # is a plain, inert Pydantic value with no execution capability.
    action = NextAuthorizedActionPolicy.derive(
        current_phase=Phase.READINESS, blocking_condition=None, target_phase=Phase.IMPLEMENTATION
    )

    assert not hasattr(action, "execute")
    assert not hasattr(action, "run")
