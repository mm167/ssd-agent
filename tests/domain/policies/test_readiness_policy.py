from __future__ import annotations

import pytest

from sdd_agent.diagnostics.errors import WorkflowViolation
from sdd_agent.domain.models.enums import Condition, ProblemClassification
from sdd_agent.domain.policies.readiness import ReadinessPolicy, dependencies_satisfied


def test_dependencies_satisfied_true_when_all_closed() -> None:
    assert dependencies_satisfied(["T001", "T002"], closed_task_ids={"T001", "T002", "T003"})


def test_dependencies_satisfied_false_when_one_missing() -> None:
    assert not dependencies_satisfied(["T001", "T002"], closed_task_ids={"T001"})


def test_dependencies_satisfied_ignores_numeric_order() -> None:
    # T005 depends on T002, not T003/T004: order in the id list is irrelevant.
    assert dependencies_satisfied(["T002"], closed_task_ids={"T004", "T003", "T002"})


def test_ready_when_all_facts_satisfied() -> None:
    decision = ReadinessPolicy.evaluate(dependency_contract_valid=True, dependencies_satisfied=True)

    assert decision.ready_for_code is True
    assert decision.condition is None


def test_repository_mismatch_blocks_before_anything_else() -> None:
    decision = ReadinessPolicy.evaluate(
        dependency_contract_valid=False,
        dependencies_satisfied=False,
        artifact_ambiguity=ProblemClassification.PRODUCT,
        repository_mismatch=True,
    )

    assert decision.ready_for_code is False
    assert decision.condition is Condition.REPOSITORY_MISMATCH


def test_invalid_dependency_contract_routes_to_tasks_required() -> None:
    decision = ReadinessPolicy.evaluate(dependency_contract_valid=False, dependencies_satisfied=True)

    assert decision.ready_for_code is False
    assert decision.condition is Condition.TASKS_REQUIRED


def test_unsatisfied_dependency_routes_to_task_dependency_unsatisfied() -> None:
    decision = ReadinessPolicy.evaluate(dependency_contract_valid=True, dependencies_satisfied=False)

    assert decision.ready_for_code is False
    assert decision.condition is Condition.TASK_DEPENDENCY_UNSATISFIED


def test_product_ambiguity_routes_to_spec_required() -> None:
    decision = ReadinessPolicy.evaluate(
        dependency_contract_valid=True,
        dependencies_satisfied=True,
        artifact_ambiguity=ProblemClassification.PRODUCT,
    )

    assert decision.ready_for_code is False
    assert decision.condition is Condition.SPEC_REQUIRED


def test_architecture_ambiguity_routes_to_plan_required() -> None:
    decision = ReadinessPolicy.evaluate(
        dependency_contract_valid=True,
        dependencies_satisfied=True,
        artifact_ambiguity=ProblemClassification.ARCHITECTURE,
    )

    assert decision.condition is Condition.PLAN_REQUIRED


def test_tasks_ambiguity_routes_to_tasks_required() -> None:
    decision = ReadinessPolicy.evaluate(
        dependency_contract_valid=True,
        dependencies_satisfied=True,
        artifact_ambiguity=ProblemClassification.TASKS,
    )

    assert decision.condition is Condition.TASKS_REQUIRED


def test_ready_for_code_never_carries_a_condition() -> None:
    decision = ReadinessPolicy.evaluate(dependency_contract_valid=True, dependencies_satisfied=True)

    assert decision.ready_for_code and decision.condition is None


def test_not_ready_always_carries_a_condition() -> None:
    decision = ReadinessPolicy.evaluate(dependency_contract_valid=False, dependencies_satisfied=True)

    assert not decision.ready_for_code and decision.condition is not None


@pytest.mark.parametrize(
    "classification",
    [ProblemClassification.CODE, ProblemClassification.ENVIRONMENT, ProblemClassification.REPOSITORY_MISMATCH],
)
def test_incompatible_artifact_ambiguity_classification_is_rejected(
    classification: ProblemClassification,
) -> None:
    # T005-IR-002: SPEC Section 14 restricts READINESS artifact ambiguity to
    # PRODUCT/ARCHITECTURE/TASKS. CODE/ENVIRONMENT/REPOSITORY_MISMATCH must be
    # explicitly rejected, not silently converted into a normal route.
    with pytest.raises(WorkflowViolation):
        ReadinessPolicy.evaluate(
            dependency_contract_valid=True,
            dependencies_satisfied=True,
            artifact_ambiguity=classification,
        )


def test_incompatible_artifact_ambiguity_never_produces_fix_required() -> None:
    with pytest.raises(WorkflowViolation):
        ReadinessPolicy.evaluate(
            dependency_contract_valid=True,
            dependencies_satisfied=True,
            artifact_ambiguity=ProblemClassification.CODE,
        )
    # No ReadinessDecision escaping with condition=FIX_REQUIRED is ever
    # produced for this input: the call above raised before constructing one.


def test_compatible_artifact_ambiguity_classifications_still_work() -> None:
    # Confirms the fix did not narrow the *valid* domain, only rejected the
    # incompatible one.
    for classification, expected in (
        (ProblemClassification.PRODUCT, Condition.SPEC_REQUIRED),
        (ProblemClassification.ARCHITECTURE, Condition.PLAN_REQUIRED),
        (ProblemClassification.TASKS, Condition.TASKS_REQUIRED),
    ):
        decision = ReadinessPolicy.evaluate(
            dependency_contract_valid=True,
            dependencies_satisfied=True,
            artifact_ambiguity=classification,
        )
        assert decision.condition is expected
