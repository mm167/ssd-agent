from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdd_agent.domain.models import EvidenceContext


def test_requires_task_and_attempt_id() -> None:
    with pytest.raises(ValidationError):
        EvidenceContext(attempt_id="a1")  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        EvidenceContext(task_id="T002")  # type: ignore[call-arg]


def test_rejects_empty_task_id() -> None:
    with pytest.raises(ValidationError):
        EvidenceContext(task_id="", attempt_id="a1")


def test_candidate_and_artifact_identity_are_optional() -> None:
    context = EvidenceContext(task_id="T002", attempt_id="a1")

    assert context.candidate_id is None
    assert context.artifact_contract_identity is None


def test_is_frozen() -> None:
    context = EvidenceContext(task_id="T002", attempt_id="a1")

    with pytest.raises(ValidationError):
        context.task_id = "T003"  # type: ignore[misc]


def test_applies_to_exact_match() -> None:
    a = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")
    b = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")

    assert a.applies_to(b)


def test_applies_to_false_on_candidate_change() -> None:
    reviewed = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")
    current = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c2")

    assert not reviewed.applies_to(current)


def test_applies_to_false_on_attempt_change() -> None:
    previous_attempt = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")
    new_attempt = EvidenceContext(task_id="T002", attempt_id="a2", candidate_id="c1")

    assert not previous_attempt.applies_to(new_attempt)


def test_applies_to_none_only_matches_none() -> None:
    no_candidate_yet = EvidenceContext(task_id="T002", attempt_id="a1")
    has_candidate = EvidenceContext(task_id="T002", attempt_id="a1", candidate_id="c1")

    assert not no_candidate_yet.applies_to(has_candidate)
    assert not has_candidate.applies_to(no_candidate_yet)
