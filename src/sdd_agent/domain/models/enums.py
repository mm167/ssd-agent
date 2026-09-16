"""Closed value sets shared by domain evidence and workflow-representation
models (TASKS T002 Scope: "Severity, routing, validation result, CI status,
and completion status closed value sets").

These enums fix the *vocabulary*; the *behavior* that decides which value
applies in a given situation (gate policies, routing policies, classification)
belongs to T005 and later TASKS, not to this module.
"""

from __future__ import annotations

from enum import StrEnum


class Phase(StrEnum):
    """Where an Attempt is in its lifecycle (PLAN Section 9.1)."""

    READINESS = "readiness"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    REVIEW = "review"
    FIX = "fix"
    RE_REVIEW = "re_review"
    READY_TO_COMMIT = "ready_to_commit"
    COMMIT = "commit"
    PUSH = "push"
    CI = "ci"
    CLOSED = "closed"
    ABANDONED = "abandoned"


class Condition(StrEnum):
    """A situation affecting progression; not necessarily a Phase (PLAN Section
    9.2; SPEC Section 47 BLOCKED examples)."""

    SPEC_REQUIRED = "spec_required"
    PLAN_REQUIRED = "plan_required"
    TASKS_REQUIRED = "tasks_required"
    FIX_REQUIRED = "fix_required"
    ENVIRONMENT_BLOCKED = "environment_blocked"
    REPOSITORY_MISMATCH = "repository_mismatch"
    TASK_DEPENDENCY_UNSATISFIED = "task_dependency_unsatisfied"


class ProblemClassification(StrEnum):
    """The nature of a problem requiring routing (SPEC Section 7; PLAN Section
    42 ProblemClassifier core classifications).

    Distinct from `sdd_agent.diagnostics.errors.TechnicalErrorCategory`, which
    classifies *technical* failures, not SDD workflow problems (PLAN Section
    87).
    """

    PRODUCT = "product"
    ARCHITECTURE = "architecture"
    TASKS = "tasks"
    CODE = "code"
    ENVIRONMENT = "environment"
    REPOSITORY_MISMATCH = "repository_mismatch"


class FindingSeverity(StrEnum):
    """Review finding severity. Exactly these three (SPEC Section 28)."""

    BLOCKER = "blocker"
    IMPORTANT = "important"
    MINOR = "minor"


class FindingRoute(StrEnum):
    """Where an actionable review finding may be routed (SPEC Section 29; PLAN
    Section 39). Deliberately excludes REPOSITORY_MISMATCH: a mismatch is
    detected structurally, not raised as a review finding (SPEC Section 48)."""

    PRODUCT = "product"
    ARCHITECTURE = "architecture"
    TASKS = "tasks"
    CODE = "code"
    ENVIRONMENT = "environment"


class ValidationStatus(StrEnum):
    """Core validation result statuses. Exactly these three (SPEC Section 19;
    PLAN Section 33)."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


class WaiverEligibleCause(StrEnum):
    """The only cause classification V1 permits for waiver eligibility (SPEC
    Section 22.2)."""

    ENVIRONMENT = "environment"


class CIStatus(StrEnum):
    """Provider-neutral CI status model. Exactly these six (PLAN Section 49)."""

    PENDING = "pending"
    RUNNING = "running"
    GREEN = "green"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_FOUND = "not_found"


class ImplementationCompletionStatus(StrEnum):
    """Closed completion statuses for ImplementationReport (PLAN Section 90A)."""

    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class HumanDecisionType(StrEnum):
    """Categories of structured human decisions (PLAN Section 54)."""

    PRODUCT = "product"
    ARCHITECTURE = "architecture"
    TASKS = "tasks"
    VALIDATION_WAIVER = "validation_waiver"
    REPOSITORY_MISMATCH_RESOLUTION = "repository_mismatch_resolution"
    COMMIT_APPROVAL = "commit_approval"
    RESTART = "restart"
    ABANDON = "abandon"
