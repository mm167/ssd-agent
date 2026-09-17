"""Core domain models and evidence contracts (TASKS T002; SPEC candidate,
validation evidence, waiver applicability, review findings, human decisions,
CI evidence, and gate-semantics identity; PLAN Sections 9, 10, 12, 15, 18, 25,
26, 28, 31, 36, 39, 49, 62, 63, 64, 90A).

This package defines data contracts and their own internal (model-level)
invariants only. Persistence (T003), Git-derived candidate computation (T004),
gate/policy behavior and routing decisions (T005), validation execution
(T006), agent execution (T007/T009/T010/T011), human-decision orchestration
(T012), commit/push/remote verification (T013), and CI provider integration
(T014/T015/T016) are out of scope here.
"""

from sdd_agent.domain.models.attempt import Attempt, NextAuthorizedAction
from sdd_agent.domain.models.agent import (
    AgentExecutionStatus,
    AgentReportType,
    AgentRequest,
    AgentResult,
    AgentStructuredReport,
    build_successful_agent_result,
    report_type_for,
)
from sdd_agent.domain.models.candidate import (
    CandidateEntry,
    CandidateEntryKind,
    CandidateIdentity,
    CandidateSnapshot,
)
from sdd_agent.domain.models.ci import CIResult
from sdd_agent.domain.models.enums import (
    CIStatus,
    Condition,
    FindingRoute,
    FindingSeverity,
    HumanDecisionType,
    ImplementationCompletionStatus,
    Phase,
    ProblemClassification,
    ValidationStatus,
    WaiverEligibleCause,
)
from sdd_agent.domain.models.event import WorkflowEvent
from sdd_agent.domain.models.git_status import WorktreeStatus
from sdd_agent.domain.models.human_decision import HumanDecision
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.implementation import ImplementationReport
from sdd_agent.domain.models.readiness import ReadinessReport
from sdd_agent.domain.models.review import Finding, ReviewReport
from sdd_agent.domain.models.schema import CURRENT_SCHEMA_VERSION, SchemaVersioned
from sdd_agent.domain.models.validation import (
    ValidationObligation,
    ValidationResult,
    ValidationWaiver,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "Attempt",
    "AgentExecutionStatus",
    "AgentReportType",
    "AgentRequest",
    "AgentResult",
    "AgentStructuredReport",
    "CIResult",
    "CIStatus",
    "CandidateEntry",
    "CandidateEntryKind",
    "CandidateIdentity",
    "CandidateSnapshot",
    "Condition",
    "EvidenceContext",
    "Finding",
    "FindingRoute",
    "FindingSeverity",
    "HumanDecision",
    "HumanDecisionType",
    "ImplementationCompletionStatus",
    "ImplementationReport",
    "NextAuthorizedAction",
    "Phase",
    "ProblemClassification",
    "ReadinessReport",
    "ReviewReport",
    "SchemaVersioned",
    "ValidationObligation",
    "ValidationResult",
    "ValidationStatus",
    "ValidationWaiver",
    "WaiverEligibleCause",
    "WorkflowEvent",
    "WorktreeStatus",
    "build_successful_agent_result",
    "report_type_for",
]
