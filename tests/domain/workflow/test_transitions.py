from __future__ import annotations

import pytest

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.domain.models.enums import Phase
from sdd_agent.domain.workflow.transitions import authorize_transition, valid_targets


def test_happy_path_transitions_are_authorized() -> None:
    happy_path = [
        (Phase.READINESS, Phase.IMPLEMENTATION),
        (Phase.IMPLEMENTATION, Phase.VALIDATION),
        (Phase.VALIDATION, Phase.REVIEW),
        (Phase.REVIEW, Phase.READY_TO_COMMIT),
        (Phase.READY_TO_COMMIT, Phase.COMMIT),
        (Phase.COMMIT, Phase.PUSH),
        (Phase.PUSH, Phase.CI),
        (Phase.CI, Phase.CLOSED),
    ]
    for current, target in happy_path:
        authorize_transition(current, target)  # must not raise


def test_fix_re_review_cycle_is_authorized() -> None:
    authorize_transition(Phase.REVIEW, Phase.FIX)
    authorize_transition(Phase.FIX, Phase.VALIDATION)
    authorize_transition(Phase.VALIDATION, Phase.RE_REVIEW)
    authorize_transition(Phase.RE_REVIEW, Phase.READY_TO_COMMIT)


def test_ci_code_failure_returns_to_fix() -> None:
    authorize_transition(Phase.CI, Phase.FIX)


def test_implementation_cannot_skip_validation_directly_to_review() -> None:
    # SPEC Section 18: "There is no valid direct transition IMPLEMENTATION ->
    # REVIEW without VALIDATION."
    with pytest.raises(WorkflowViolation):
        authorize_transition(Phase.IMPLEMENTATION, Phase.REVIEW)


def test_readiness_cannot_jump_directly_to_commit() -> None:
    with pytest.raises(WorkflowViolation):
        authorize_transition(Phase.READINESS, Phase.COMMIT)


def test_fix_cannot_skip_validation_directly_to_re_review() -> None:
    with pytest.raises(WorkflowViolation):
        authorize_transition(Phase.FIX, Phase.RE_REVIEW)


def test_closed_is_terminal() -> None:
    assert valid_targets(Phase.CLOSED) == frozenset()
    with pytest.raises(WorkflowViolation):
        authorize_transition(Phase.CLOSED, Phase.READINESS)


def test_abandoned_is_terminal() -> None:
    assert valid_targets(Phase.ABANDONED) == frozenset()
    with pytest.raises(WorkflowViolation):
        authorize_transition(Phase.ABANDONED, Phase.IMPLEMENTATION)


def test_every_non_terminal_phase_may_be_abandoned() -> None:
    for phase in Phase:
        if phase in (Phase.CLOSED, Phase.ABANDONED):
            continue
        authorize_transition(phase, Phase.ABANDONED)  # must not raise


@pytest.mark.parametrize(
    "phase",
    [
        Phase.IMPLEMENTATION,
        Phase.VALIDATION,
        Phase.REVIEW,
        Phase.RE_REVIEW,
        Phase.READY_TO_COMMIT,
        Phase.CI,
    ],
)
def test_artifact_return_eligible_phases_may_return_to_readiness(phase: Phase) -> None:
    # SPEC Sections 16, 20, 29, 35.6, 41-44; PLAN Section 90: an approved
    # artifact change invalidates dependent evidence and the workflow
    # returns through READINESS, never directly to FIX.
    authorize_transition(phase, Phase.READINESS)


@pytest.mark.parametrize("phase", [Phase.COMMIT, Phase.PUSH])
def test_commit_and_push_cannot_return_directly_to_readiness(phase: Phase) -> None:
    with pytest.raises(WorkflowViolation):
        authorize_transition(phase, Phase.READINESS)


def test_no_force_or_skip_bypass_parameter_exists() -> None:
    import inspect

    signature = inspect.signature(authorize_transition)
    assert set(signature.parameters) == {"current", "target"}


def test_invalid_transition_raises_explicit_error_with_diagnostic_details() -> None:
    with pytest.raises(WorkflowViolation) as excinfo:
        authorize_transition(Phase.READINESS, Phase.CLOSED)

    assert excinfo.value.details == {"current_phase": "readiness", "target_phase": "closed"}
